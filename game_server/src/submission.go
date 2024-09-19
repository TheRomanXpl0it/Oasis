package main

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"game/db"
	"game/log"
	"math"
	"net/http"
	"sync"
	"time"

	"github.com/uptrace/bun"
)

type SubResp struct {
	Msg    string `json:"msg"`
	Flag   string `json:"flag"`
	Status bool   `json:"status"`
}

// Crate a map of lock for each team
var lockMap map[string]*sync.RWMutex = make(map[string]*sync.RWMutex)
var lockMappingMutex sync.Mutex
var lastSubmissionTime map[string]time.Time = make(map[string]time.Time)
var scoreMutex sync.Mutex

func Values[M ~map[K]V, K comparable, V any](m M) []V {
	r := make([]V, 0, len(m))
	for _, v := range m {
		r = append(r, v)
	}
	return r
}

func Contains[T comparable](s []T, e T) bool {
	for _, v := range s {
		if v == e {
			return true
		}
	}
	return false
}

var scale float64 = 15 * math.Sqrt(5.0)
var norm float64 = math.Log(math.Log(5.0)) / 12.0

func elaborateFlag(team string, flag string, resp *SubResp) {
	var ctx context.Context = context.Background()
	info := new(db.Flag)
	err := conn.NewSelect().Model(info).Where("id = ?", flag).Scan(ctx)
	if err != nil {
		resp.Msg += "Denied: invalid flag"
		log.Debugf("Flag %s from %s: invalid", flag, team)
		return
	}
	if info.Team == conf.Teams[conf.Nop] {
		resp.Msg += "Denied: flag from nop team"
		log.Debugf("Flag %s from %s: from nop team", flag, team)
		return
	}
	if info.Team == team {
		resp.Msg += "Denied: flag is your own"
		log.Debugf("Flag %s from %s: is your own", flag, team)
		return
	}
	if time.Since(info.CreatedAt) > conf.FlagExpireTime {
		resp.Msg += "Denied: flag too old"
		log.Debugf("Flag %s from %s: too old", flag, team)
		return
	}

	flagSubmission := new(db.FlagSubmission)
	if err = conn.NewSelect().Model(flagSubmission).Where("team = ? and flag_id = ?", team, info.ID).Scan(ctx); err != nil {
		if err != sql.ErrNoRows {
			log.Panicf("Error fetching flag submission: %v", err)
		}
	} else {
		resp.Msg += "Denied: flag already submitted"
		log.Debugf("Flag %s from %s: already submitted", flag, team)
		return
	}

	// Calculate flag points in a db transaction to avoid inconsistencies on db
	scoreMutex.Lock()
	var offensePoints float64
	err = conn.RunInTx(ctx, nil, func(ctx context.Context, tx bun.Tx) error {
		attackerScore := new(db.ServiceScore)
		victimScore := new(db.ServiceScore)
		if err := conn.NewSelect().Model(attackerScore).Where("team = ? and service = ?", team, info.Service).Scan(ctx); err != nil {
			return err
		}
		if err := conn.NewSelect().Model(victimScore).Where("team = ? and service = ?", info.Team, info.Service).Scan(ctx); err != nil {
			return err
		}
		offensePoints = scale / (1 + math.Exp((math.Sqrt(attackerScore.Points)-math.Sqrt(victimScore.Points))*norm))
		defensePoints := min(victimScore.Points, offensePoints)

		_, err = conn.NewInsert().Model(&db.FlagSubmission{
			FlagID:          info.ID,
			Team:            team,
			OffensivePoints: offensePoints,
			DefensivePoints: defensePoints,
		}).Exec(ctx)
		if err != nil {
			return err
		}
		if _, err := conn.NewUpdate().Model(attackerScore).WherePK().Set("points = points + ?", offensePoints).Exec(ctx); err != nil {
			return err
		}
		if _, err := conn.NewUpdate().Model(victimScore).WherePK().Set("points = points - ?", defensePoints).Exec(ctx); err != nil {
			return err
		}

		return nil
	})
	scoreMutex.Unlock()

	if err != nil {
		resp.Msg += "Denied: internal error"
		log.Errorf("Error submitting flag: %v", err)
		return
	}

	resp.Status = true
	resp.Msg += fmt.Sprintf("Accepted: %f flag points", offensePoints)
	log.Debugf("Flag %s from %s: %.02f flag points", flag, team, offensePoints)
}

func elaborateFlags(team string, submittedFlags []string) []SubResp {
	responses := make([]SubResp, 0, len(submittedFlags))
	for _, flag := range submittedFlags {
		resp := SubResp{
			Flag:   flag,
			Status: false,
			Msg:    fmt.Sprintf("[%s] ", flag),
		}
		elaborateFlag(team, flag, &resp)
		responses = append(responses, resp)
	}
	return responses
}

func submitFlags(w http.ResponseWriter, r *http.Request) {
	teamToken := r.Header.Get("X-Team-Token")

	if teamToken == "" || !Contains(Values(conf.Teams), teamToken) || teamToken == conf.Teams[conf.Nop] {
		w.WriteHeader(http.StatusUnauthorized)
		return
	}

	team := ""
	for ip, t := range conf.Teams {
		if t == teamToken {
			team = ip
			break
		}
	}
	if team == "" {
		panic("Team not found on submitter (unexpected)")
	}

	// Checking if team lock exists, if not create it
	lockMappingMutex.Lock()
	if lockMap[team] == nil {
		lockMap[team] = new(sync.RWMutex)
	}
	lockMappingMutex.Unlock()
	// Locking the team avoiding multiple submission at the same time
	lockMap[team].Lock()
	defer lockMap[team].Unlock()

	if conf.SubmitterLimit != nil {
		//Get last time
		lastSubmitTime, ok := lastSubmissionTime[team]
		if ok {
			//Check if the time has passed
			if time.Since(lastSubmitTime) < conf.SubmitterLimitTime {
				log.Infof("Submission limit reached for team %s", team)
				w.WriteHeader(http.StatusTooManyRequests)
				return
			}
		}
		lastSubmissionTime[team] = time.Now()
	}

	var submittedFlags []string
	dec := json.NewDecoder(r.Body)
	if err := dec.Decode(&submittedFlags); err != nil {
		w.WriteHeader(http.StatusBadRequest)
		return
	}

	submittedFlags = submittedFlags[:min(len(submittedFlags), conf.MaxFlagsPerRequest)]
	responses := elaborateFlags(team, submittedFlags)

	enc := json.NewEncoder(w)
	if err := enc.Encode(responses); err != nil {
		w.WriteHeader(http.StatusInternalServerError)
	}
}

func serveSubmission() {
	mux := http.NewServeMux()
	mux.HandleFunc("PUT /flags", submitFlags)

	log.Noticef("Starting flag_submission on :8080")
	if err := http.ListenAndServe("0.0.0.0:8080", mux); err != nil {
		log.Fatalf("Error serving flag_submission: %v", err)
	}
}
