package main

import (
	"encoding/json"
	"fmt"
	"game/log"
	"math"
	"net/http"
	"time"
)

type SubResp struct {
	Msg    string `json:"msg"`
	Flag   string `json:"flag"`
	Status bool   `json:"status"`
}

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

const maxFlags = 2000

func elaborateFlag(team string, flag string, resp *SubResp) {
	flags.RLock()
	info, ok := flags.flags[flag]
	flags.RUnlock()
	if !ok {
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
	if time.Now().After(info.Expire) {
		resp.Msg += "Denied: flag too old"
		log.Debugf("Flag %s from %s: too old", flag, team)
		return
	}
	stolenFlags.RLock()
	if stolenFlags.flags[team][info.Service][flag] {
		stolenFlags.RUnlock()
		resp.Msg += "Denied: flag already claimed"
		log.Debugf("Flag %s from %s: already claimed", flag, team)
		return
	}
	stolenFlags.RUnlock()

	score.Lock()
	stolenFlags.Lock()
	lostFlags.Lock()

	stolenFlags.flags[team][info.Service][flag] = true
	lostFlags.flags[info.Team][info.Service][flag] = true
	offensePoints := scale / (1 + math.Exp((math.Sqrt(score.score[team][info.Service])-math.Sqrt(score.score[info.Team][info.Service]))*norm))
	defensePoints := min(score.score[info.Team][info.Service], offensePoints)
	score.score[team][info.Service] += offensePoints
	score.score[info.Team][info.Service] -= defensePoints

	lostFlags.Unlock()
	stolenFlags.Unlock()
	score.Unlock()

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
	team := r.Header.Get("X-Team-Token")
	if team == "" || !Contains(Values(conf.Teams), team) || team == conf.Teams[conf.Nop] {
		w.WriteHeader(http.StatusUnauthorized)
		return
	}

	if conf.SubmitterLimit != nil {
		lastSubmits.RLock()
		if last, ok := lastSubmits.times[team]; ok && time.Now().Before(last.Add(time.Duration((*conf.SubmitterLimit)*int64(time.Millisecond)))) {
			lastSubmits.RUnlock()
			log.Infof("Submission limit reached for team %s", team)
			w.WriteHeader(http.StatusTooManyRequests)
			return
		}
		lastSubmits.times[team] = time.Now()
		lastSubmits.RUnlock()
	}

	var submittedFlags []string
	dec := json.NewDecoder(r.Body)
	if err := dec.Decode(&submittedFlags); err != nil {
		w.WriteHeader(http.StatusBadRequest)
		return
	}

	submittedFlags = submittedFlags[:min(len(submittedFlags), maxFlags)]
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
