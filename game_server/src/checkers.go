package main

import (
	"bytes"
	"context"
	"fmt"
	"game/log"
	"math/rand"
	"net"
	"os/exec"
	"sort"
	"sync"
	"time"
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
	for {
		for range flagLen - 1 {
			index := randSrc.Intn(len(letters))
			flag += string(letters[index])
		}
		flags.RLock()
		if _, ok := flags.flags[flag]; !ok {
			flags.RUnlock()
			break
		}
		flags.RUnlock()
		log.Warningf("Flag generation collision: %s", flag)
		flag = ""
	}
	return flag + "="
}

func genCheckFlag(team string, service string) string {
	flag := genFlag()
	flags.Lock()
	flags.flags[flag] = FlagInfo{
		Team:    team,
		Service: service,
		Expire:  time.Now().Add(conf.RoundLen * 5),
	}
	log.Debugf("NEW FLAG %v -> %+v", flag, flags.flags[flag])
	flags.Unlock()
	return flag
}

func runChecker(team string, service string, params *CheckerParams, ctx context.Context) int {
	cmd := exec.CommandContext(ctx, "python3", conf.CheckerDir+service+"/checker.py")
	cmd.Env = append(cmd.Env, "TOKEN="+conf.Token)
	cmd.Env = append(cmd.Env, "ACTION="+params.Action)
	cmd.Env = append(cmd.Env, "TEAM_ID="+params.TeamID)
	cmd.Env = append(cmd.Env, "ROUND="+params.Round)
	cmd.Env = append(cmd.Env, "FLAG="+params.Flag)

	// TODO: extract stderr
	//cmd.Stderr = os.Stdout

	if err := cmd.Start(); err != nil {
		log.Criticalf("Error running checker %v:%v on %v: %v", team, params.TeamID, service, err)
		return CRITICAL
	}

	err := cmd.Wait()
	if err == nil {
		log.Criticalf("Error checker status %v:%v on %v: no exit status", team, params.TeamID, service)
		return CRITICAL
	}

	exiterr, ok := err.(*exec.ExitError)
	if !ok {
		log.Criticalf("Error waiting for checker %v:%v on %v: %v", team, params.TeamID, service, err)
		return CRITICAL
	}

	var color string
	exitCode := exiterr.ExitCode()
	switch exitCode {
	case OK:
		color = log.GREEN
	case DOWN:
		color = log.RED
	case ERROR:
		color = log.HIGH_RED
	case KILLED:
		color = log.PURPLE
	default:
		log.Criticalf("Error unknown checker status %v:%v on %v: %v", team, params.TeamID, service, exitCode)
		return CRITICAL
	}

	log.Infof("Checker status %v: %v%v%v from %v:%v on %v", params.Action, color, exitCode, log.END, team, params.TeamID, service)
	return exitCode
}

func checkerRoutine() {
	var (
		currentRound int = 0
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
		teams[i] = conf.Teams[ip.String()]
	}

	for {
		ctx, cancel := context.WithTimeout(context.Background(), conf.RoundLen)
		waitGroup.Add(len(teams) * len(conf.Services))
		for i, team := range teams {
			for _, service := range conf.Services {

				go func(i int, team string, service string, waitGroup *sync.WaitGroup) {
					defer waitGroup.Done()
					timeout1 := time.Duration(rand.Intn(int(conf.Round/1000)/4)) * time.Second
					timeout2 := time.Duration(rand.Intn(int(conf.Round/1000)/4)) * time.Second
					timeout3 := time.Duration(rand.Intn(int(conf.Round/1000)/4)) * time.Second

					time.Sleep(timeout1)
					params := &CheckerParams{}
					params.Round = fmt.Sprint(currentRound)
					params.TeamID = fmt.Sprint(i)
					flag := genCheckFlag(team, service)
					params.Flag = flag

					// TODO: runchecker status history
					params.Action = CHECK_SLA
					status := runChecker(team, service, params, ctx)
					if status != OK {
						ticksDown.Lock()
						ticksDown.ticks[team][service]++
						ticksDown.last[team][service] = false
						ticksDown.Unlock()
						return
					}

					time.Sleep(timeout2)
					params.Action = PUT_FLAG
					status = runChecker(team, service, params, ctx)
					if status != OK {
						ticksDown.Lock()
						ticksDown.ticks[team][service]++
						ticksDown.last[team][service] = false
						ticksDown.Unlock()
						return
					}

					time.Sleep(timeout3)
					params.Action = GET_FLAG
					status = runChecker(team, service, params, ctx)
					if status != OK {
						ticksDown.Lock()
						ticksDown.ticks[team][service]++
						ticksDown.last[team][service] = false
						ticksDown.Unlock()
						return
					}

					ticksUp.Lock()
					ticksUp.ticks[team][service]++
					ticksUp.Unlock()
					ticksDown.Lock()
					ticksDown.last[team][service] = true
					ticksDown.Unlock()
				}(i, team, service, &waitGroup)
			}
		}

		waitGroup.Wait()
		<-ctx.Done()
		cancel()

		computeScores()
		totalScore.RLock()
		log.Noticef("Scores on %v Round: %+v", currentRound, totalScore.score)
		totalScore.RUnlock()
		currentRound++
	}
}
