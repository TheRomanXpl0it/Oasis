package main

import (
	"bytes"
	"context"
	"database/sql"
	"fmt"
	"game/db"
	"game/log"
	"math/rand"
	"net"
	"os/exec"
	"path/filepath"
	"sort"
	"strings"
	"sync"
	"time"

	"github.com/uptrace/bun"
)

type CheckerParams struct {
	Action string
	TeamID string
	Round  string
	Flag   string
}

const flagLen = 32

const (
	OK       = 101
	DOWN     = 104
	ERROR    = 110
	KILLED   = -1
	CRITICAL = 1337
)

const (
	CHECK_SLA = "CHECK_SLA"
	PUT_FLAG  = "PUT_FLAG"
	GET_FLAG  = "GET_FLAG"
)

var randSrc *rand.Rand

func initRand() {
	randSrc = rand.New(rand.NewSource(time.Now().UnixNano()))
}

func genFlag() string {
	letters := "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
	var flag string
	for range flagLen - 1 {
		index := randSrc.Intn(len(letters))
		flag += string(letters[index])
	}
	return flag + "="
}

func genCheckFlag(team string, service string, round uint) string {
	var ctx context.Context = context.Background()
	for {
		flag := genFlag()
		_, err := conn.NewInsert().Model(&db.Flag{
			ID:      flag,
			Team:    team,
			Round:   round,
			Service: service,
		}).Exec(ctx)
		if err != nil {
			if strings.Contains(strings.ToLower(err.Error()), "duplicate") {
				log.Debugf("DUPLICATE FLAG %v -> %+v", flag, team)
			} else {
				log.Criticalf("Error inserting flag %v:%v on %v: %v", team, flag, service, err)
			}
		} else {
			log.Debugf("NEW FLAG %v -> %+v", flag, team)
			return flag
		}
	}
}

func runChecker(team string, service string, params *CheckerParams, ctx context.Context) (int, string) {
	cmd := exec.CommandContext(ctx, "python3", "checker.py")
	cmd.Env = append(cmd.Env, "TOKEN="+conf.Token)
	cmd.Env = append(cmd.Env, "ACTION="+params.Action)
	cmd.Env = append(cmd.Env, "TEAM_ID="+params.TeamID)
	cmd.Env = append(cmd.Env, "ROUND="+params.Round)
	cmd.Env = append(cmd.Env, "FLAG="+params.Flag)
	cmd.Env = append(cmd.Env, "SERVICE="+service)
	cmd.Env = append(cmd.Env, "TERM=xterm")

	workingDir, err := filepath.Abs("../checkers/" + service)
	if err != nil {
		log.Criticalf("Error getting working directory for checker %v %v:%v on %v: %v", params.Action, team, params.TeamID, service, err)
		return CRITICAL, "Checker system error"
	}
	cmd.Dir = workingDir

	var outb, errb bytes.Buffer
	cmd.Stdout = &outb
	cmd.Stderr = &errb

	if err := cmd.Start(); err != nil {
		log.Criticalf("Error running checker %v %v:%v on %v: %v", params.Action, team, params.TeamID, service, err)
		return CRITICAL, "Checker system error"
	}

	if err = cmd.Wait(); err == nil {
		log.Criticalf("Error checker status %v %v:%v on %v: no exit status", params.Action, team, params.TeamID, service)
		return CRITICAL, "Checker system error"
	}

	msg := outb.String()

	log.Infof("Checker %v %v:%v on %v output: %v", params.Action, team, params.TeamID, service, errb.String())

	exiterr, ok := err.(*exec.ExitError)
	if !ok {
		log.Criticalf("Error waiting for checker %v %v:%v on %v: %v", params.Action, team, params.TeamID, service, err)
		return CRITICAL, "Checker system error"
	}

	var color string
	exitCode := exiterr.ExitCode()
	switch exitCode {
	case OK:
		color = log.GREEN
		msg = "Everything is ok"
	case DOWN:
		color = log.RED
	case ERROR:
		color = log.HIGH_RED
	case KILLED:
		color = log.PURPLE
	default:
		log.Infof("Checker unknown status %v: %v%v%v from %v:%v on %v", params.Action, color, exitCode, log.END, team, params.TeamID, service)
		return ERROR, msg
	}

	log.Infof("Checker status %v: %v%v%v from %v:%v on %v", params.Action, color, exitCode, log.END, team, params.TeamID, service)
	return exitCode, msg
}

func calcRoundStartTime(round uint) time.Time {
	return conf.GameStartTime.Add(time.Duration(int64(conf.RoundLen) * int64(round)))
}

func remainingTimeFromRound(round uint) time.Duration {
	return time.Until(calcRoundStartTime(round))
}

func waitForRound(round uint) {
	timeToWait := time.Until(calcRoundStartTime(round))
	if timeToWait > 0 {
		time.Sleep(timeToWait)
	}
}

// return error if the flag is already submitted
func calcSLA(team string, service string) (sla float64, totSla uint, upSla uint, err error) {
	var ctx context.Context = context.Background()
	totQuery := conn.NewSelect().Model((*db.StatusHistory)(nil)).ColumnExpr("count(id)").Where("team = ? and service = ? and put_flag_status != ? and get_flag_status != ? and check_status != ?", team, service, CRITICAL, CRITICAL, CRITICAL)
	upQuery := conn.NewSelect().Model((*db.StatusHistory)(nil)).ColumnExpr("count(id)").Where("team = ? and service = ? and put_flag_status = ? and get_flag_status = ? and check_status = ?", team, service, OK, OK, OK)
	if err := conn.NewSelect().ColumnExpr("(?)", totQuery).ColumnExpr("(?)", upQuery).Scan(ctx, &totSla, &upSla); err != nil {
		log.Errorf("Error fetching sla status: %v", err)
		return 0.0, 0, 0, err
	}
	if totSla == 0 {
		return 1.0, 0, 0, nil
	}
	return float64(upSla) / float64(totSla), totSla, upSla, nil
}

func checkerRoutine() {
	var (
		currentRound uint = 0
		waitGroup    sync.WaitGroup
	)

	realIPs := make([]net.IP, 0, len(conf.Teams))
	for ip := range conf.Teams {
		realIPs = append(realIPs, net.ParseIP(ip))
	}
	sort.Slice(realIPs, func(i, j int) bool {
		return bytes.Compare(realIPs[i], realIPs[j]) < 0
	})
	teams := make([]string, len(realIPs))
	for i, ip := range realIPs {
		teams[i] = ip.String()
	}

	if conf.GameEndTime != nil && time.Now().After(*conf.GameEndTime) {
		log.Infof("Game ended")
		if err := CtfRouteLock(); err != nil {
			log.Errorf("Error locking routes: %v", err)
		}
		return
	}

	preUnlocked := false

	if time.Now().After(conf.GameStartTime) {
		//Game already started
		log.Infof("Game already started!")
		if err := CtfRouteUnlock(); err != nil {
			log.Errorf("Error unlocking routes: %v", err)
		}
		preUnlocked = true
		currentRound = uint(time.Since(conf.GameStartTime) / conf.RoundLen)
	}

	if currentRound > 0 {
		lastRoundExposed := db.GetExposedRound()
		//Delating data after the last round exposed (probably uncompleted)
		if _, err := conn.NewDelete().Model((*db.Flag)(nil)).Where("round > ?", lastRoundExposed).Exec(context.Background()); err != nil {
			log.Criticalf("Error deleting flags for round %v: %v", currentRound, err)
		}
		if _, err := conn.NewDelete().Model((*db.StatusHistory)(nil)).Where("round > ?", lastRoundExposed).Exec(context.Background()); err != nil {
			log.Criticalf("Error deleting status for round %v: %v", currentRound, err)
		}
		//Wait for the next round (probably game server restarted)
		currentRound++
	}

	waitForRound(currentRound) // Wait for the first/next round
	if !preUnlocked {
		if err := CtfRouteUnlock(); err != nil {
			log.Errorf("Error unlocking routes: %v", err)
		}
	}
	log.Infof("Starting checker loop with round %v", currentRound)

	for {
		if conf.GameEndTime != nil && time.Now().After(*conf.GameEndTime) {
			log.Infof("Game ended")
			if err := CtfRouteLock(); err != nil {
				log.Errorf("Error locking routes: %v", err)
			}
			break
		}
		timeForNextRound := int64(remainingTimeFromRound(currentRound+1)) / int64(time.Millisecond)
		ctx, cancel := context.WithTimeout(context.Background(), time.Duration(timeForNextRound)*time.Millisecond)
		waitGroup.Add(len(teams) * len(conf.Services))
		for i, team := range teams {
			for _, service := range conf.Services {

				go func(teamId int, team string, service string, waitGroup *sync.WaitGroup, maxTimeout int64) {
					defer waitGroup.Done()

					var checkersWaitGroup sync.WaitGroup
					var statusHistoryLock sync.Mutex

					validFlags := make([]db.Flag, 0)
					if err := conn.NewSelect().Model(&validFlags).Where("team = ? and service = ? and ? - round < ?", team, service, currentRound, conf.FlagExpireTicks).Scan(ctx); err != nil {
						log.Errorf("Error fetching valid flags: %v", err)
						return
					}

					newFlag := genCheckFlag(team, service, currentRound)

					statusData := db.StatusHistory{
						Team:    team,
						Service: service,
						Round:   currentRound,
						// Default values for get flag that colud never be called in some checks
						GetFlagStatus:  OK,
						GetFlagMessage: "There was no flag to check",
						GetFlagAt:      time.Now(),
					}

					checkersWaitGroup.Add(len(validFlags) + 2)
					for j := range len(validFlags) + 2 {
						flag := newFlag
						if j >= 2 {
							flag = validFlags[j-2].ID
						}
						action := GET_FLAG
						if j == 0 {
							action = PUT_FLAG
						}
						if j == 1 {
							action = CHECK_SLA
						}
						go func() {
							defer checkersWaitGroup.Done()

							params := &CheckerParams{
								Round:  fmt.Sprint(currentRound),
								TeamID: fmt.Sprint(teamId),
								Flag:   flag,
								Action: action,
							}
							//Random timeout to avoid all checkers to run at the same time and to avoid timing detection
							time.Sleep(time.Duration(rand.Intn(int(float64(maxTimeout)/1.15))) * time.Millisecond)

							status, msg := runChecker(team, service, params, ctx)

							statusHistoryLock.Lock()
							defer statusHistoryLock.Unlock()
							if action == PUT_FLAG {
								statusData.PutFlagStatus = status
								statusData.PutFlagMessage = msg
								statusData.PutFlagAt = time.Now()
								if status != OK {
									//Delete the flag if the put failed
									if _, err := conn.NewDelete().Model(&db.Flag{}).Where("id = ?", flag).Exec(ctx); err != nil {
										log.Criticalf("Error deleting flag %v:%v on %v: %v", team, teamId, service, err)
									}
								}
							} else if action == GET_FLAG {
								if statusData.GetFlagStatus == OK { // If at least 1 check failed, don't overwrite the status
									statusData.GetFlagStatus = status
									statusData.GetFlagMessage = msg
									statusData.GetFlagAt = time.Now()
								}
							} else if action == CHECK_SLA {
								statusData.CheckStatus = status
								statusData.CheckMessage = msg
								statusData.CheckdAt = time.Now()
							}

						}()
					}

					checkersWaitGroup.Wait()
					waitForRound(currentRound) // Wait for the end of the round before updating the database

					dbctx := context.Background()
					err := conn.RunInTx(dbctx, nil, func(dbctx context.Context, tx bun.Tx) error {
						_, err := conn.NewInsert().Model(&statusData).Exec(dbctx)
						if err != nil {
							log.Criticalf("Error inserting sla status %v:%v on %v: %v", team, teamId, service, err)
							return err
						}
						if statusData.Sla, statusData.SlaTotTimes, statusData.SlaUpTimes, err = calcSLA(team, service); err != nil {
							log.Criticalf("Error calculating sla %v:%v on %v: %v", team, teamId, service, err)
							return err
						}
						if err := conn.NewSelect().ColumnExpr("score").Model((*db.ServiceScore)(nil)).Where("team = ? and service = ?", team, service).Scan(dbctx, &statusData.Score); err != nil {
							log.Criticalf("Error fetching score %v:%v on %v: %v", team, teamId, service, err)
							return err
						}

						if err = conn.NewSelect().Model((*db.FlagSubmission)(nil)).ColumnExpr("count(*)").Join("JOIN flags flag ON flag.id = submit.flag_id").Where("submit.team = ? and flag.service = ?", team, service).Scan(dbctx, &statusData.StolenFlags); err != nil {
							if err != sql.ErrNoRows {
								log.Panicf("Error fetching stolen flags: %v", err)
								return err
							}
						}

						if err = conn.NewSelect().Model((*db.FlagSubmission)(nil)).ColumnExpr("count(*)").Join("JOIN flags flag ON flag.id = submit.flag_id").Where("flag.team = ? and flag.service = ?", team, service).Scan(dbctx, &statusData.LostFlags); err != nil {
							if err != sql.ErrNoRows {
								log.Panicf("Error fetching lost flags: %v", err)
								return err
							}
						}

						if _, err = conn.NewUpdate().Model(&statusData).Where("team = ? and service = ? and round = ?", team, service, currentRound).Exec(dbctx); err != nil {
							log.Criticalf("Error updating sla status %v:%v on %v: %v", team, teamId, service)
							return err
						}

						return nil
					})

					if err != nil {
						log.Criticalf("Error inserting status %v:%v on %v: %v", team, teamId, service, err)
					}

				}(i, team, service, &waitGroup, timeForNextRound)
			}
		}

		waitGroup.Wait()
		<-ctx.Done()
		cancel()
		currentRound++
		waitForRound(currentRound)
		db.SetExposedRound(int64(currentRound - 1))
	}
}
