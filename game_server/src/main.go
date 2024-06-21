package main

import (
	"os"
	"os/signal"

	"game/log"
)

func main() {
	var err error

	conf, err = LoadConfig("config.yml")
	if err != nil {
		log.Fatalf("Error loading config: %v", err)
	}

	if conf.Logfile != "" {
		log.SetLogFile(conf.Logfile)
		defer log.CloseLogFile()
	}
	log.SetLogLevel(conf.LogLevel)
	log.Debugf("Config: %+v\n", conf)

	initRand()
	initScoreData()
	initFlagIDs()

	go serveFlagIDs()
	go serveSubmission()
	go serveScoreboard()
	go checkerRoutine()

	stop := make(chan os.Signal, 1)
	signal.Notify(stop, os.Interrupt)
	log.Infof("Game Server is now running. Press CTRL-C to exit.")
	<-stop
}
