package main

import (
	"game/log"
	"os"
	"os/signal"
	"syscall"
)

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
