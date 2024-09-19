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
	StolenFlags   int
	LostFlags     int
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

// return error if the flag is already submitted
func calcSLA(team string, service string) (totalSlas float64, totSla int, upSla int, err error) {
	var ctx context.Context = context.Background()
	totSla = 0
	upSla = 0
	totQuery := conn.NewSelect().Model((*db.SlaStatus)(nil)).ColumnExpr("count(id)").Where("team = ? and service = ? and flag_in_status != ? and flag_out_status != ? and check_status != ?", team, service, ERROR, ERROR, ERROR)
	upQuery := conn.NewSelect().Model((*db.SlaStatus)(nil)).ColumnExpr("count(id)").Where("team = ? and service = ? and flag_in_status = ? and flag_out_status = ? and check_status = ?", team, service, OK, OK, OK)
	if err := conn.NewSelect().ColumnExpr("(?)", totQuery).ColumnExpr("(?)", upQuery).Scan(ctx, &totSla, &upSla); err != nil {
		log.Errorf("Error fetching sla status: %v", err)
		return 0.0, 0, 0, err
	}
	if totSla == 0 {
		return 1.0, 0, 0, nil
	}
	return float64(upSla) / float64(totSla), totSla, upSla, nil
}

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
		var totScore float64 = 0.0
		for _, service := range conf.Services {
			fetchedScore := new(db.ServiceScore)
			if err := conn.NewSelect().Model(fetchedScore).Where("team = ? and service = ?", team, service).Scan(ctx); err != nil {
				log.Panicf("Error fetching service score: %v", err)
			}
			sla, totSLA, upSLA, err := calcSLA(team, service)
			if err != nil {
				log.Panicf("Error calculating service SLA: %v", err)
			}
			stolenFlags := 0
			lostFlags := 0
			score := 0.0
			err = conn.NewSelect().Model((*db.FlagSubmission)(nil)).ColumnExpr("count(*)").Join("JOIN flags flag ON flag.id = submit.flag_id").Where("submit.team = ? and flag.service = ?", team, service).Scan(ctx, &stolenFlags)
			if err != nil {
				if err != sql.ErrNoRows {
					log.Panicf("Error fetching stolen flags: %v", err)
				}
			}

			if err = conn.NewSelect().Model((*db.FlagSubmission)(nil)).ColumnExpr("count(*)").Join("JOIN flags flag ON flag.id = submit.flag_id").Where("flag.team = ? and flag.service = ?", team, service).Scan(ctx, &lostFlags); err != nil {
				if err != sql.ErrNoRows {
					log.Panicf("Error fetching lost flags: %v", err)
				}
			}

			lastSLACheck := new(db.SlaStatus)
			lastSLACheck.CheckStatus = ERROR

			if err = conn.NewSelect().Model(lastSLACheck).Where("team = ? and service = ?", team, service).Order("flag_in_executed_at DESC").Limit(1).Scan(ctx); err != nil {
				if err != sql.ErrNoRows {
					log.Panicf("Error fetching last SLA check: %v", err)
				}
			}
			lastTickColor := "red"
			if lastSLACheck.CheckStatus == OK && lastSLACheck.FlagInStatus == OK && lastSLACheck.FlagOutStatus == OK {
				lastTickColor = "green"
			}

			score = sla * float64(fetchedScore.Points)
			t.Services[service] = TemplService{
				Name:          service,
				StolenFlags:   stolenFlags,
				LostFlags:     lostFlags,
				Score:         fmt.Sprintf("%.2f", score),
				TicksUp:       uint(upSLA),
				TicksDown:     uint(totSLA - upSLA),
				Sla:           fmt.Sprintf("%.2f", sla*100),
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
