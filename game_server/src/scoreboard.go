package main

import (
	"bytes"
	"context"
	"database/sql"
	"fmt"
	"game/db"
	"game/log"
	"html/template"
	"net"
	"net/http"
	"sort"
)

type TemplService struct {
	Name          string
	StolenFlags   uint
	LostFlags     uint
	Score         string
	TicksUp       uint
	TicksDown     uint
	Sla           string
	LastTickColor string
	LastTick      bool
}

type TemplTeam struct {
	Team       string
	Services   map[string]TemplService
	TotalScore string
}

/*
/api/chart
[
	{
		"round": 1,
		"scores": [
			{
				"team": "10.60.0.1",
				"score": 0.0,
			},
			{...}
		]
	},
	{...}
]


/api/scoreboard
{

	"round": 1,
	"scores": [
		{
			"team": "10.60.0.1",
			"image": "url",
			"score": 0.0,
			"services": [
				{
					"service": "service1",
					"stolen_flags": 0,
					"lost_flags": 0,
					"sla": 100.0,
					"points": 0.0,
					"ticks_up": 0,
					"ticks_down": 0,
					"put_flag": 101,
					"put_flag_msg": "msg",
					"get_flag": 101,
					"get_flag_msg": "msg",
					"sla_check": 101,
					"sla_check_msg": "msg",
				}
			]
		}
	]
}

/api/team/{team}
[
	{

		"round": 1,
		"scores": [
			{
				"team": "10.60.0.1",
				"image": "url",
				"score": 0.0,
				"services": [
					{
						"service": "service1",
						"stolen_flags": 0,
						"lost_flags": 0,
						"sla": 100.0,
						"points": 0.0,
						"ticks_up": 0,
						"ticks_down": 0,
						"put_flag": 101,
						"put_flag_msg": "msg",
						"get_flag": 101,
						"get_flag_msg": "msg",
						"sla_check": 101,
						"sla_check_msg": "msg",
					}
				]
			}
		]
	}
]

/api/config
{
	"teams":[
		{
			"name": "team1",
			"host": "10.60.0.1",
			"image": "url",
			"nop": false
		},{...}
	]
	"services":[
		"service1",
		"service2",
		...
	],
	"start_time": "",
	"round_len": 60000,
	"flag_expire_ticks": 5,
	"submitter_flags_limit": 2000,
	"submitter_rate_limit": 10000,
}
*/

func handleScoreboard(w http.ResponseWriter, r *http.Request) {
	var ctx context.Context = context.Background()
	tmpl := template.Must(template.ParseFiles("templates/index.html"))

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
		t := TemplTeam{
			Team:       team,
			Services:   make(map[string]TemplService),
			TotalScore: "0",
		}
		round := db.GetExposedRound()
		var totScore float64 = 0.0
		for _, service := range conf.Services {
			lastScore := new(db.StatusHistory)
			lastScore.CheckStatus = ERROR

			if err := conn.NewSelect().Model(lastScore).Where("team = ? and service = ? and round = ?", team, service, round).Scan(ctx); err != nil {
				if err != sql.ErrNoRows {
					log.Panicf("Error fetching last SLA check: %v", err)
				}
			}
			lastTickColor := "red"
			if lastScore.CheckStatus == OK && lastScore.FlagInStatus == OK && lastScore.FlagOutStatus == OK {
				lastTickColor = "green"
			}

			score := lastScore.ActualSla * float64(lastScore.ActualScore)
			t.Services[service] = TemplService{
				Name:          service,
				StolenFlags:   lastScore.StolenFlags,
				LostFlags:     lastScore.LostFlags,
				Score:         fmt.Sprintf("%.2f", score),
				TicksUp:       lastScore.SlaUpTimes,
				TicksDown:     lastScore.SlaTotTimes - lastScore.SlaUpTimes,
				Sla:           fmt.Sprintf("%.2f", lastScore.ActualSla*100),
				LastTickColor: lastTickColor,
				LastTick:      lastTickColor == "green",
			}
			totScore += score
		}
		t.TotalScore = fmt.Sprintf("%.2f", totScore)
		teams["Teams"] = append(teams["Teams"], t)

	}

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
