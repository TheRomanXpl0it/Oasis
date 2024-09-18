package main

import (
	"encoding/json"
	"fmt"
	"game/log"
	"net/http"
	"sync"
)

type FlagIDSub struct {
	Token     string      `json:"token"`
	ServiceID string      `json:"serviceId"`
	TeamID    string      `json:"teamId"`
	Round     int         `json:"round"`
	FlagID    interface{} `json:"flagId"`
}

type FlagIDs struct {
	sync.RWMutex
	ids map[string]map[string][]interface{}
}

var flagIDs FlagIDs // flagIDs[service][team] = []flagID

func initFlagIDs() {
	flagIDs.ids = make(map[string]map[string][]interface{})
	for _, service := range conf.Services {
		flagIDs.ids[service] = make(map[string][]interface{})
		for team := range conf.Teams {
			flagIDs.ids[service][team] = make([]interface{}, 0)
		}
	}
}

func submitFlagID(w http.ResponseWriter, r *http.Request) {
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

	flagIDs.RLock()
	if _, ok := flagIDs.ids[sub.ServiceID]; !ok {
		http.Error(w, "Invalid service", http.StatusBadRequest)
		log.Errorf("Error: invalid service in flag_id submission: %+v", sub)
		flagIDs.RUnlock()
		return
	}
	flagIDs.RUnlock()

	var team string
	_, ok := conf.Teams[sub.TeamID]
	if !ok {
		team = fmt.Sprintf("10.60.%s.1", sub.TeamID)
	} else {
		team = sub.TeamID
	}

	flagIDs.Lock()
	if len(flagIDs.ids[sub.ServiceID][team]) > 4 {
		flagIDs.ids[sub.ServiceID][team] = flagIDs.ids[sub.ServiceID][team][1:]
	}

	flagIDs.ids[sub.ServiceID][team] = append(flagIDs.ids[sub.ServiceID][team], sub.FlagID)
	flagIDs.Unlock()
	log.Debugf("Received flag_id %v from %v:%v (%v) in round %v",
		sub.FlagID, sub.TeamID, team, sub.ServiceID, sub.Round)
}

func retriveFlagIDs(w http.ResponseWriter, r *http.Request) {
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

	flagIDs.RLock()
	defer flagIDs.RUnlock()

	if !ok_service && !ok_team {
		if err := enc.Encode(flagIDs.ids); err != nil {
			http.Error(w, "Internal server error", http.StatusInternalServerError)
			log.Errorf("Error encoding flag_ids: %v", err)
			return
		}

	} else if !ok_service {
		teamIDs := make(map[string][]interface{})
		for service, serviceIDs := range flagIDs.ids {
			teamIDs[service] = serviceIDs[team[0]]
		}
		if err := enc.Encode(teamIDs); err != nil {
			http.Error(w, "Internal server error", http.StatusInternalServerError)
			log.Errorf("Error encoding flag_ids: %v", err)
			return
		}

	} else if !ok_team {
		serviceIDs := flagIDs.ids[services[0]]
		if err := enc.Encode(serviceIDs); err != nil {
			http.Error(w, "Internal server error", http.StatusInternalServerError)
			log.Errorf("Error encoding flag_ids: %v", err)
			return
		}

	} else {
		serviceIDs := flagIDs.ids[services[0]]
		teamIDs := serviceIDs[team[0]]
		if err := enc.Encode(teamIDs); err != nil {
			http.Error(w, "Internal server error", http.StatusInternalServerError)
			log.Errorf("Error encoding flag_ids: %v", err)
			return
		}
	}

	log.Debugf("Received flag_ids request %v", query)
}

func serveFlagIDs() {
	mux := http.NewServeMux()

	mux.HandleFunc("POST /postFlagId", submitFlagID)
	mux.HandleFunc("GET /flagIds", retriveFlagIDs)

	log.Noticef("Starting flag_ids server on :8081")
	if err := http.ListenAndServe("0.0.0.0:8081", mux); err != nil {
		log.Fatalf("Failed to start flag_ids server: %v", err)
	}
}
