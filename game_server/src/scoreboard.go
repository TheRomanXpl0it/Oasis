package main

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"game/db"
	"game/log"
	"html/template"
	"net"
	"net/http"
	"os"
	"path/filepath"
	"sort"
	"time"

	"github.com/gorilla/mux"
)

/*
{
	"service": "service1",
	"stolen_flags": 0,
	"lost_flags": 0,
	"sla": 100.0,
	"score": 0.0,
	"ticks_up": 0,
	"ticks_down": 0,
	"put_flag": 101,
	"put_flag_msg": "msg",
	"get_flag": 101,
	"get_flag_msg": "msg",
	"sla_check": 101,
	"sla_check_msg": "msg",
	"final_score": 0.0,
}

*/

type ServiceRoundStatus struct {
	Service     string  `json:"service"`
	StolenFlags uint    `json:"stolen_flags"`
	LostFlags   uint    `json:"lost_flags"`
	Sla         float64 `json:"sla"`
	Score       float64 `json:"score"`
	TicksUp     uint    `json:"ticks_up"`
	TicksDown   uint    `json:"ticks_down"`
	PutFlag     int     `json:"put_flag"`
	PutFlagMsg  string  `json:"put_flag_msg"`
	GetFlag     int     `json:"get_flag"`
	GetFlagMsg  string  `json:"get_flag_msg"`
	SlaCheck    int     `json:"sla_check"`
	SlaCheckMsg string  `json:"sla_check_msg"`
	FinalScore  float64 `json:"final_score"`
}

/*
{
	"team": "10.60.0.1",
	"score": 0.0,
}
*/

type TeamRoundStatusShort struct {
	Team  string  `json:"team"`
	Score float64 `json:"score"`
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
*/

type ChartAPIResponse struct {
	Round  uint                   `json:"round"`
	Scores []TeamRoundStatusShort `json:"scores"`
}

func handleChart(w http.ResponseWriter, r *http.Request) {
	round := db.GetExposedRound()
	if round < 0 {
		if err := json.NewEncoder(w).Encode([]ChartAPIResponse{}); err != nil {
			log.Errorf("Error encoding response: %v", err)
			http.Error(w, "Internal server error", http.StatusInternalServerError)
			return
		}
	}
	response := make([]ChartAPIResponse, round+1)
	dbScores := new([]db.StatusHistory)
	ctx := context.Background()
	for i := 0; i <= int(round); i++ {
		if err := conn.NewSelect().Model(dbScores).Where("round = ?", i).Scan(ctx); err != nil {
			log.Errorf("Error fetching scores for round %d: %v", i, err)
			http.Error(w, "Internal server error", http.StatusInternalServerError)
			return
		}
		scores := make([]TeamRoundStatusShort, 0, len(conf.Teams))
		for _, score := range *dbScores {
			scoresTeamIndex := -1
			for j, team := range scores {
				if team.Team == score.Team {
					scoresTeamIndex = j
					break
				}
			}
			if scoresTeamIndex != -1 {
				scores[scoresTeamIndex].Score += score.Score * score.Sla
			} else {
				scores = append(scores, TeamRoundStatusShort{
					Team:  score.Team,
					Score: score.Score * score.Sla,
				})
			}
		}
		response[i] = ChartAPIResponse{
			Round:  uint(i),
			Scores: scores,
		}
	}

	if err := json.NewEncoder(w).Encode(response); err != nil {
		log.Errorf("Error encoding response: %v", err)
		http.Error(w, "Internal server error", http.StatusInternalServerError)
		return
	}

}

/*
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
					"score": 0.0,
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
*/

type TeamRoundStatus struct {
	Team     string               `json:"team"`
	Image    string               `json:"image"`
	Score    float64              `json:"score"`
	Services []ServiceRoundStatus `json:"services"`
}

type ScoreboardAPIResponse struct {
	Round  uint              `json:"round"`
	Scores []TeamRoundStatus `json:"scores"`
}

func handleScoreboard(w http.ResponseWriter, r *http.Request) {

	round := db.GetExposedRound()

	if round < 0 {
		if err := json.NewEncoder(w).Encode(ScoreboardAPIResponse{
			Round:  0,
			Scores: make([]TeamRoundStatus, 0),
		}); err != nil {
			log.Errorf("Error encoding response: %v", err)
			http.Error(w, "Internal server error", http.StatusInternalServerError)
			return
		}
	}

	response := ScoreboardAPIResponse{
		Round:  uint(round),
		Scores: make([]TeamRoundStatus, 0, len(conf.Teams)),
	}

	ctx := context.Background()
	for team := range conf.Teams {
		scoreData := new([]db.StatusHistory)
		if err := conn.NewSelect().Model(scoreData).Where("team = ? and round = ?", team, round).Scan(ctx); err != nil {
			log.Errorf("Error fetching scores for team %s: %v", team, err)
			http.Error(w, "Internal server error", http.StatusInternalServerError)
			return
		}
		services := make([]ServiceRoundStatus, 0, len(conf.Services))
		totScore := 0.0
		for _, service := range *scoreData {
			services = append(services, ServiceRoundStatus{
				Service:     service.Service,
				StolenFlags: service.StolenFlags,
				LostFlags:   service.LostFlags,
				Sla:         service.Sla,
				Score:       service.Score,
				TicksUp:     service.SlaUpTimes,
				TicksDown:   service.SlaTotTimes - service.SlaUpTimes,
				PutFlag:     service.PutFlagStatus,
				PutFlagMsg:  service.PutFlagMessage,
				GetFlag:     service.GetFlagStatus,
				GetFlagMsg:  service.GetFlagMessage,
				SlaCheck:    service.CheckStatus,
				SlaCheckMsg: service.CheckMessage,
				FinalScore:  service.Score * service.Sla,
			})
			totScore += service.Score * service.Sla
		}
		response.Scores = append(response.Scores, TeamRoundStatus{
			Team:     team,
			Image:    "",
			Score:    totScore,
			Services: services,
		})
	}

	if err := json.NewEncoder(w).Encode(response); err != nil {
		log.Errorf("Error encoding response: %v", err)
		http.Error(w, "Internal server error", http.StatusInternalServerError)
		return
	}

}

/*
/api/team/{team}
[
	{

		"round": 1,
		"score": {
			"team": "10.60.0.1",
			"image": "url",
			"score": 0.0,
			"services": [
				{
					"service": "service1",
					"stolen_flags": 0,
					"lost_flags": 0,
					"sla": 100.0,
					"score": 0.0,
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
	}
]
*/

type TeamAPIResponse struct {
	Round uint            `json:"round"`
	Score TeamRoundStatus `json:"score"`
}

func handleTeam(w http.ResponseWriter, r *http.Request) {
	team := "10.60." + mux.Vars(r)["team_id"] + ".1"
	if _, ok := conf.Teams[team]; !ok {
		http.Error(w, "Invalid team", http.StatusBadRequest)
		log.Errorf("Error: invalid team %v", team)
		return
	}
	round := db.GetExposedRound()
	if round < 0 {
		if err := json.NewEncoder(w).Encode([]TeamAPIResponse{}); err != nil {
			log.Errorf("Error encoding response: %v", err)
			http.Error(w, "Internal server error", http.StatusInternalServerError)
			return
		}
	}

	response := make([]TeamAPIResponse, round+1)
	ctx := context.Background()
	for i := 0; i <= int(round); i++ {
		scoreData := new([]db.StatusHistory)
		if err := conn.NewSelect().Model(scoreData).Where("team = ? and round = ?", team, i).Scan(ctx); err != nil {
			log.Errorf("Error fetching scores for team %s: %v", team, err)
			http.Error(w, "Internal server error", http.StatusInternalServerError)
			return
		}
		services := make([]ServiceRoundStatus, 0, len(conf.Services))
		totalScore := 0.0
		for _, service := range *scoreData {
			services = append(services, ServiceRoundStatus{
				Service:     service.Service,
				StolenFlags: service.StolenFlags,
				LostFlags:   service.LostFlags,
				Sla:         service.Sla,
				Score:       service.Score,
				TicksUp:     service.SlaUpTimes,
				TicksDown:   service.SlaTotTimes - service.SlaUpTimes,
				PutFlag:     service.PutFlagStatus,
				PutFlagMsg:  service.PutFlagMessage,
				GetFlag:     service.GetFlagStatus,
				GetFlagMsg:  service.GetFlagMessage,
				SlaCheck:    service.CheckStatus,
				SlaCheckMsg: service.CheckMessage,
				FinalScore:  service.Score * service.Sla,
			})
			totalScore += service.Score * service.Sla
		}
		response[i] = TeamAPIResponse{
			Round: uint(i),
			Score: TeamRoundStatus{
				Team:     team,
				Image:    "",
				Score:    totalScore,
				Services: services,
			},
		}

	}

	if err := json.NewEncoder(w).Encode(response); err != nil {
		log.Errorf("Error encoding response: %v", err)
		http.Error(w, "Internal server error", http.StatusInternalServerError)
		return
	}

}

/*
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

type TeamConfig struct {
	Name  string `json:"name"`
	Host  string `json:"host"`
	Image string `json:"image"`
	Nop   bool   `json:"nop"`
}

type ConfigAPIResponse struct {
	Teams               []TeamConfig `json:"teams"`
	Services            []string     `json:"services"`
	StartTime           string       `json:"start_time"`
	RoundLen            uint         `json:"round_len"`
	FlagExpireTicks     uint         `json:"flag_expire_ticks"`
	SubmitterFlagsLimit uint         `json:"submitter_flags_limit"`
	SubmitterRateLimit  uint         `json:"submitter_rate_limit"`
}

func handleConfig(w http.ResponseWriter, r *http.Request) {
	teams := make([]TeamConfig, 0, len(conf.Teams))
	for ip, team := range conf.Teams {
		teams = append(teams, TeamConfig{
			Name:  "team-" + ip,
			Host:  ip,
			Image: "",
			Nop:   team == conf.Teams[conf.Nop],
		})
	}
	if err := json.NewEncoder(w).Encode(ConfigAPIResponse{
		Teams:               teams,
		Services:            conf.Services,
		StartTime:           conf.GameStartTime.Format(time.RFC3339),
		RoundLen:            uint(conf.RoundLen / time.Millisecond),
		FlagExpireTicks:     uint(conf.FlagExpireTicks),
		SubmitterFlagsLimit: uint(conf.MaxFlagsPerRequest),
		SubmitterRateLimit:  uint(*conf.SubmitterLimit),
	}); err != nil {
		log.Errorf("Error encoding response: %v", err)
		http.Error(w, "Internal server error", http.StatusInternalServerError)
		return
	}
}

// spaHandler implements the http.Handler interface, so we can use it
// to respond to HTTP requests. The path to the static directory and
// path to the index file within that static directory are used to
// serve the SPA in the given static directory.
type spaHandler struct {
	staticPath string
	indexPath  string
}

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

func handleOldScoreboard(w http.ResponseWriter, r *http.Request) {
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
			if lastScore.CheckStatus == OK && lastScore.PutFlagStatus == OK && lastScore.GetFlagStatus == OK {
				lastTickColor = "green"
			}

			score := lastScore.Sla * float64(lastScore.Score)
			t.Services[service] = TemplService{
				Name:          service,
				StolenFlags:   lastScore.StolenFlags,
				LostFlags:     lastScore.LostFlags,
				Score:         fmt.Sprintf("%.2f", score),
				TicksUp:       lastScore.SlaUpTimes,
				TicksDown:     lastScore.SlaTotTimes - lastScore.SlaUpTimes,
				Sla:           fmt.Sprintf("%.2f", lastScore.Sla*100),
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

// ServeHTTP inspects the URL path to locate a file within the static dir
// on the SPA handler. If a file is found, it will be served. If not, the
// file located at the index path on the SPA handler will be served. This
// is suitable behavior for serving an SPA (single page application).
func (h spaHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	// Join internally call path.Clean to prevent directory traversal
	path := filepath.Join(h.staticPath, r.URL.Path)

	// check whether a file exists or is a directory at the given path
	fi, err := os.Stat(path)
	if os.IsNotExist(err) || fi.IsDir() {
		// file does not exist or path is a directory, serve index.html
		http.ServeFile(w, r, filepath.Join(h.staticPath, h.indexPath))
		return
	}

	if err != nil {
		// if we got an error (that wasn't that the file doesn't exist) stating the
		// file, return a 500 internal server error and stop
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	// otherwise, use http.FileServer to serve the static file
	http.FileServer(http.Dir(h.staticPath)).ServeHTTP(w, r)
}

func serveScoreboard() {
	router := mux.NewRouter()

	router.HandleFunc("/api/scoreboard", handleScoreboard).Methods("GET")
	router.HandleFunc("/api/chart", handleChart).Methods("GET")
	router.HandleFunc("/api/team/{team_id}", handleTeam).Methods("GET")
	router.HandleFunc("/api/config", handleConfig).Methods("GET")
	router.HandleFunc("/", handleOldScoreboard).Methods("GET")

	log.Noticef("Starting flag_ids server on :80")
	spa := spaHandler{staticPath: "frontend", indexPath: "index.html"}
	router.PathPrefix("/new/").Handler(spa)

	srv := &http.Server{
		Handler:      router,
		Addr:         "0.0.0.0:80",
		WriteTimeout: 30 * time.Second,
		ReadTimeout:  30 * time.Second,
	}

	log.Fatal(srv.ListenAndServe())

}
