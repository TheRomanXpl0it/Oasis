package main

import (
	"os"
	"time"

	"gopkg.in/yaml.v3"
)

type Config struct {
	RoundLen   time.Duration
	LogLevel   string            `yaml:"log_level"`
	Logfile    string            `yaml:"log_file"`
	Round      int64             `yaml:"round_len"`
	Token      string            `yaml:"token"`
	Nop        string            `yaml:"nop"`
	Teams      map[string]string `yaml:"teams"`
	Services   []string          `yaml:"services"`
	CheckerDir string            `yaml:"checker_dir"`
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

	return c, nil
}
