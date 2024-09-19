package main

import (
	"context"
	"database/sql"
	"game/db"
	"game/log"
	"os"
	"os/signal"
	"syscall"

	"github.com/uptrace/bun"
)

var conn *bun.DB

func initScoreboard() {
	var ctx context.Context = context.Background()
	log.Debugf("Initializing scoreboard")

	for team := range conf.Teams {
		for _, service := range conf.Services {
			fetchedScore := new(db.ServiceScore)
			err := conn.NewSelect().Model(fetchedScore).Where("team = ? and service = ?", team, service).Scan(ctx)
			if err != nil {
				if err == sql.ErrNoRows {
					_, err := conn.NewInsert().Model(&db.ServiceScore{
						Team:    team,
						Service: service,
						Points:  conf.InitialServicePoints,
					}).Exec(ctx)
					if err != nil {
						log.Panicf("Error inserting service score %v", err)
					}
				} else {
					log.Panicf("Error fetching service score %v", err)
				}
			}
		}
	}

}

func main() {
	var err error

	conf, err = LoadConfig("config.yml")
	if err != nil {
		log.Fatalf("Error loading config: %v", err)
	}
	log.Debugf("Config: %+v\n", conf)

	go serveFlagIDs()
	go serveSubmission()
	go serveScoreboard()
	go checkerRoutine()

	stop := make(chan os.Signal, 1)
	signal.Notify(stop, os.Interrupt)
	signal.Notify(stop, syscall.SIGTERM)
	signal.Notify(stop, syscall.SIGINT)
	signal.Notify(stop, syscall.SIGQUIT)
	log.Infof("Game Server is now running. Press CTRL-C to exit.")
	<-stop
}
