package main

import (
	"bytes"
	"game/log"
	"html/template"
	"net"
	"net/http"
	"sort"
)

type TemplService struct {
	Name          string
	StolenFlags   int
	LostFlags     int
	Score         int
	TicksUp       uint
	TicksDown     uint
	Sla           int
	LastTickColor string
	LastTick      bool
}

type TemplTeam struct {
	Team       string
	Services   map[string]TemplService
	TotalScore int
}

func handleScoreboard(w http.ResponseWriter, r *http.Request) {
	tmpl := template.Must(template.ParseFiles("templates/index.html"))

	stolenFlags.RLock()
	lostFlags.RLock()
	score.RLock()
	ticksUp.RLock()
	ticksDown.RLock()
	sla.RLock()
	totalScore.RLock()

	realIPs := make([]net.IP, 0, len(conf.Teams))
	for ip := range conf.Teams {
		realIPs = append(realIPs, net.ParseIP(ip))
	}
	sort.Slice(realIPs, func(i, j int) bool {
		return bytes.Compare(realIPs[i], realIPs[j]) < 0
	})
	sortedTeams := make([]string, len(realIPs))
	for i, ip := range realIPs {
		sortedTeams[i] = ip.String()
	}

	teams := map[string][]TemplTeam{
		"Teams": make([]TemplTeam, 0, len(conf.Teams)),
	}
	for _, team := range sortedTeams {
		teamToken := conf.Teams[team]
		t := TemplTeam{
			Team:       team,
			Services:   make(map[string]TemplService),
			TotalScore: int(totalScore.score[teamToken]),
		}
		for _, service := range conf.Services {
			var color string
			if ticksDown.last[teamToken][service] {
				color = "green"
			} else {
				color = "red"
			}
			t.Services[service] = TemplService{
				Name:          service,
				StolenFlags:   len(stolenFlags.flags[teamToken][service]),
				LostFlags:     len(lostFlags.flags[teamToken][service]),
				Score:         int(score.score[teamToken][service] * sla.score[teamToken][service]),
				TicksUp:       ticksUp.ticks[teamToken][service],
				TicksDown:     ticksDown.ticks[teamToken][service],
				Sla:           int(sla.score[teamToken][service] * 100),
				LastTickColor: color,
				LastTick:      ticksDown.last[teamToken][service],
			}
		}
		teams["Teams"] = append(teams["Teams"], t)
	}

	stolenFlags.RUnlock()
	lostFlags.RUnlock()
	score.RUnlock()
	ticksUp.RUnlock()
	ticksDown.RUnlock()
	sla.RUnlock()
	totalScore.RUnlock()

	tmpl.Execute(w, teams)
}

func serveScoreboard() {
	mux := http.NewServeMux()

	mux.HandleFunc("/", handleScoreboard)

	log.Noticef("Starting flag_ids server on :80")
	if err := http.ListenAndServe("0.0.0.0:80", mux); err != nil {
		log.Fatalf("Error serving scoreboard: %v", err)
	}
}
