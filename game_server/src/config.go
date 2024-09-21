package main

import (
	"game/db"
	"game/log"
	"os"
	"time"

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
	LogLevel            string              `yaml:"log_level"`
	Round               int64               `yaml:"round_len"`
	Token               string              `yaml:"token"`
	Nop                 string              `yaml:"nop"`
	Teams               map[string]TeamInfo `yaml:"teams"`
	Services            []string            `yaml:"services"`
	CheckerDir          string              `yaml:"checker_dir"`
	FlagExpireTicks     int64               `yaml:"flag_expire_ticks"`
	InitialServiceScore float64             `yaml:"initial_service_score"`
	SubmitterLimit      *int64              `yaml:"submitter_limit,omitempty"`
	MaxFlagsPerRequest  int                 `yaml:"max_flags_per_request"`
	Debug               bool                `yaml:"debug"`
}

var conf *Config

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
	if err = dec.Decode(&c); err != nil {
		return c, err
	}

	c.RoundLen = time.Duration(c.Round) * time.Millisecond
	if c.SubmitterLimit != nil {
		c.SubmitterLimitTime = time.Duration(*c.SubmitterLimit) * time.Millisecond
	}
	conf = c
	log.SetLogLevel(conf.LogLevel)
	initRand()
	db.InitDB()
	conn = db.ConnectDB()
	initScoreboard()
	conf.GameStartTime = db.GetStartTime()

	return c, nil
}
