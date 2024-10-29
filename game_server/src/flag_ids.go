package main

import (
	"context"
	"encoding/json"
	"fmt"
	"game/db"
	"game/log"
	"net/http"
	"time"

	"github.com/gorilla/mux"
)

type FlagIDSub struct {
	Token     string      `json:"token"`
	ServiceID string      `json:"serviceId"`
	TeamID    string      `json:"teamId"`
	Round     int         `json:"round"`
	FlagID    interface{} `json:"flagId"`
}

//Needed to save on postgres also string, numbers ecc... that are not directly supported by jsonb type

func submitFlagID(w http.ResponseWriter, r *http.Request) {
	var ctx context.Context = context.Background()
	jsonDecoder := json.NewDecoder(r.Body)
	var sub FlagIDSub
	if err := jsonDecoder.Decode(&sub); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		log.Errorf("Error decoding flag_id: %v", err)
		return
	}

	if sub.Token != conf.Token || sub.ServiceID == "" || sub.TeamID == "" || sub.FlagID == "" {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		log.Errorf("Error: invalid flag_id submission: %+v", sub)
		return
	}

	var team string
	_, ok := conf.Teams[sub.TeamID]
	if !ok {
		team = fmt.Sprintf("10.60.%s.1", sub.TeamID)
	} else {
		team = sub.TeamID
	}

	var associatedFlag = new(db.Flag)
	if err := conn.NewSelect().Model(associatedFlag).Where("team = ? and round = ? and service = ?", team, sub.Round, sub.ServiceID).Scan(ctx); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		log.Errorf("Error: invalid flag_id submission: %v", err)
		return
	}

	if _, err := conn.NewUpdate().Model(associatedFlag).Set("external_flag_id = ?", db.FlagIdWrapper{K: sub.FlagID}).WherePK().Exec(ctx); err != nil {
		http.Error(w, "Internal server error", http.StatusInternalServerError)
		log.Criticalf("Error updating flag_id: %v", err)
		return
	}

	log.Debugf("Received flag_id %v from %v:%v (%v) in round %v",
		sub.FlagID, sub.TeamID, team, sub.ServiceID, sub.Round)
}

func retriveFlagIDs(w http.ResponseWriter, r *http.Request) {
	var ctx context.Context = context.Background()
	currentRound := db.GetExposedRound()
	query := r.URL.Query()

	enc := json.NewEncoder(w)

	services, ok_service := query["service"]
	if ok_service {
		if len(services) < 1 {
			ok_service = false
		} else {
			found := false
			for _, s := range conf.Services {
				if services[0] == s {
					found = true
					break
				}
			}
			if !found {
				http.Error(w, "Invalid request", http.StatusBadRequest)
				log.Errorf("Error: invalid service %v", services[0])
				return
			}
		}
	}

	team, ok_team := query["team"]
	if ok_team {
		if len(team) < 1 {
			ok_team = false
		} else {
			_, ok := conf.Teams[team[0]]
			if !ok {
				http.Error(w, "Invalid request", http.StatusBadRequest)
				log.Errorf("Error: invalid team %v", team[0])
				return
			}
		}
	}
	validFlags := make([]db.Flag, 0)
	var err error = nil
	if !ok_service && !ok_team {
		err = conn.NewSelect().Model(&validFlags).Where("? - round < ? and round <= ?", currentRound, conf.FlagExpireTicks, currentRound).Scan(ctx)
	} else if !ok_service {
		err = conn.NewSelect().Model(&validFlags).Where("team = ? and ? - round < ? and round <= ?", team[0], currentRound, conf.FlagExpireTicks, currentRound).Scan(ctx)
	} else if !ok_team {
		err = conn.NewSelect().Model(&validFlags).Where("service = ? and ? - round < ? and round <= ?", services[0], currentRound, conf.FlagExpireTicks, currentRound).Scan(ctx)
	} else {
		err = conn.NewSelect().Model(&validFlags).Where("team = ? and service = ? and ? - round < ? and round <= ?", team[0], services[0], currentRound, conf.FlagExpireTicks, currentRound).Scan(ctx)
	}

	if err != nil {
		http.Error(w, "Internal server error", http.StatusInternalServerError)
		log.Errorf("Error fetching flag_ids: %v", err)
		return
	}

	flagIDs := make(map[string]map[string][]interface{})
	for _, flag := range validFlags {
		if _, ok := flagIDs[flag.Service]; !ok {
			flagIDs[flag.Service] = make(map[string][]interface{})
		}
		if _, ok := flagIDs[flag.Service][flag.Team]; !ok {
			flagIDs[flag.Service][flag.Team] = make([]interface{}, 0)
		}
		if flag.ExternalFlagId.K == nil {
			continue
		}
		flagIDs[flag.Service][flag.Team] = append(flagIDs[flag.Service][flag.Team], flag.ExternalFlagId.K)
	}

	w.Header().Set("Content-Type", "application/json")
	if err := enc.Encode(flagIDs); err != nil {
		http.Error(w, "Internal server error", http.StatusInternalServerError)
		log.Errorf("Error encoding flag_ids: %v", err)
		return
	}

	log.Debugf("Received flag_ids request %v", query)
}

func serveFlagIDs() {
	router := mux.NewRouter()

	router.HandleFunc("/postFlagId", submitFlagID).Methods("POST")
	router.HandleFunc("/flagIds", retriveFlagIDs).Methods("GET")

	log.Noticef("Starting flag_ids server on :8081")

	srv := &http.Server{
		Handler:      router,
		Addr:         "0.0.0.0:8081",
		WriteTimeout: 30 * time.Second,
		ReadTimeout:  30 * time.Second,
	}

	log.Fatal(srv.ListenAndServe())
}
