package main

import (
	"context"
	"database/sql"
	"game/db"
	"game/log"
	"os"
	"time"

	"github.com/uptrace/bun"
	"gopkg.in/yaml.v3"
)

type TeamInfo struct {
	Token string `yaml:"token"`
	Name  string `yaml:"name"`
	Image string `yaml:"image"`
}

type Config struct {
	RoundLen            time.Duration
	SubmitterLimitTime  time.Duration
	GameStartTime       time.Time
	GameEndTime         *time.Time
	Services            []string
	LogLevel            string              `yaml:"log_level"`
	Round               int64               `yaml:"round_len"`
	Token               string              `yaml:"token"`
	Nop                 string              `yaml:"nop"`
	Teams               map[string]TeamInfo `yaml:"teams"`
	CheckerDir          string              `yaml:"checker_dir"`
	FlagExpireTicks     int64               `yaml:"flag_expire_ticks"`
	InitialServiceScore float64             `yaml:"initial_service_score"`
	SubmitterLimit      *int64              `yaml:"submitter_limit,omitempty"`
	MaxFlagsPerRequest  int                 `yaml:"max_flags_per_request"`
	Debug               bool                `yaml:"debug"`
	StartTime           *string             `yaml:"start_time"`
	EndTime             *string             `yaml:"end_time"`
}

var conf *Config
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
						Score:   conf.InitialServiceScore,
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

func LoadConfig(path string) (*Config, error) {
	c := &Config{}

	if _, err := os.Stat(path); os.IsNotExist(err) {
		return c, err
	}
	file, err := os.Open(path)
	if err != nil {
		return c, err
	}
	defer file.Close()

	dec := yaml.NewDecoder(file)
	if err = dec.Decode(c); err != nil {
		return c, err
	}
	conf = c

	conf.RoundLen = time.Duration(conf.Round) * time.Millisecond
	if conf.SubmitterLimit != nil {
		conf.SubmitterLimitTime = time.Duration(*conf.SubmitterLimit) * time.Millisecond
	}

	// Init services data
	conf.Services = make([]string, 0)
	entries, err := os.ReadDir("../checkers")
	if err != nil {
		log.Fatal(err)
	}
	for _, e := range entries {
		if e.IsDir() {
			conf.Services = append(conf.Services, e.Name())
		}
	}

	log.SetLogLevel(conf.LogLevel)
	initRand()
	db.InitDB()
	conn = db.ConnectDB()
	initScoreboard()

	if conf.StartTime != nil {
		startTime, err := time.Parse(time.RFC3339, *conf.StartTime)
		if err != nil {
			log.Panicf("Error parsing start time: %v", err)
		}
		db.SetStartTime(startTime)
	}

	conf.GameStartTime = db.GetStartTime()

	if conf.EndTime != nil {
		endTime, err := time.Parse(time.RFC3339, *conf.EndTime)
		if err != nil {
			log.Panicf("Error parsing end time: %v", err)
		}
		conf.GameEndTime = &endTime
	} else {
		conf.GameEndTime = nil
	}

	return conf, nil
}
