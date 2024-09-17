package main

import (
	"math"
	"sync"
	"time"
)

type FlagInfo struct {
	Team    string
	Service string
	Expire  time.Time
}

type SubmittedFlags struct {
	sync.RWMutex
	flags map[string]map[string]map[string]bool
}

type Ticks struct {
	sync.RWMutex
	ticks map[string]map[string]uint
	last  map[string]map[string]bool
}

type Score struct {
	sync.RWMutex
	score map[string]map[string]float64
}

type TotalScore struct {
	sync.RWMutex
	score map[string]float64
}

type Flags struct {
	sync.RWMutex
	flags map[string]FlagInfo
}

type SubmissionTimes struct {
	sync.RWMutex
	times map[string]time.Time
}

var (
	stolenFlags SubmittedFlags // stolenFlags[team][service][flag] = true
	lostFlags   SubmittedFlags // lostFlags[team][service][flag] = true
	score       Score          // score[team][service] = points
	ticksUp     Ticks          // ticksUp[team][service] = ticksUp
	ticksDown   Ticks          // ticksDown[team][service] = ticksDown
	sla         Score          // sla[team][service] = sla
	totalScore  TotalScore     // totalScore[team] = score[team] * sla[team]
	flags       Flags          // flags[flag] = FlagInfo
	lastSubmits SubmissionTimes
)

var scale float64
var norm float64

const initialScore = 5000.0

func initScoreData() {
	scale = 15 * math.Sqrt(5.0)
	norm = math.Log(math.Log(5.0)) / 12.0

	stolenFlags.Lock()
	stolenFlags.flags = make(map[string]map[string]map[string]bool)
	for _, team := range conf.Teams {
		stolenFlags.flags[team] = make(map[string]map[string]bool)
		for _, service := range conf.Services {
			stolenFlags.flags[team][service] = make(map[string]bool)
		}
	}
	stolenFlags.Unlock()

	lostFlags.Lock()
	lostFlags.flags = make(map[string]map[string]map[string]bool)
	for _, team := range conf.Teams {
		lostFlags.flags[team] = make(map[string]map[string]bool)
		for _, service := range conf.Services {
			lostFlags.flags[team][service] = make(map[string]bool)
		}
	}
	lostFlags.Unlock()

	score.Lock()
	score.score = make(map[string]map[string]float64)
	for _, team := range conf.Teams {
		score.score[team] = make(map[string]float64)
		for _, service := range conf.Services {
			score.score[team][service] = initialScore
		}
	}
	score.Unlock()

	ticksUp.Lock()
	ticksUp.ticks = make(map[string]map[string]uint)
	for _, team := range conf.Teams {
		ticksUp.ticks[team] = make(map[string]uint)
		for _, service := range conf.Services {
			ticksUp.ticks[team][service] = 0
		}
	}
	ticksUp.Unlock()

	ticksDown.Lock()
	ticksDown.ticks = make(map[string]map[string]uint)
	for _, team := range conf.Teams {
		ticksDown.ticks[team] = make(map[string]uint)
		for _, service := range conf.Services {
			ticksDown.ticks[team][service] = 0
		}
	}
	ticksDown.last = make(map[string]map[string]bool)
	for _, team := range conf.Teams {
		ticksDown.last[team] = make(map[string]bool)
		for _, service := range conf.Services {
			ticksDown.last[team][service] = true
		}
	}
	ticksDown.Unlock()

	sla.Lock()
	sla.score = make(map[string]map[string]float64)
	for _, team := range conf.Teams {
		sla.score[team] = make(map[string]float64)
		for _, service := range conf.Services {
			sla.score[team][service] = 1.0
		}
	}
	sla.Unlock()

	totalScore.Lock()
	totalScore.score = make(map[string]float64)
	for _, team := range conf.Teams {
		totalScore.score[team] = initialScore * float64(len(conf.Services))
	}
	totalScore.Unlock()

	lastSubmits.Lock()
	lastSubmits.times = make(map[string]time.Time)
	lastSubmits.Unlock()

	flags.Lock()
	flags.flags = make(map[string]FlagInfo)
	flags.Unlock()
}

func computeScores() {
	totalScore.Lock()
	score.Lock()
	sla.Lock()
	ticksUp.RLock()
	ticksDown.RLock()

	for _, team := range conf.Teams {
		totalScore.score[team] = 0.0
		for _, service := range conf.Services {
			if ticksDown.ticks[team][service]+ticksUp.ticks[team][service] == 0 {
				sla.score[team][service] = 1.0
			} else {
				sla.score[team][service] = float64(ticksUp.ticks[team][service]) /
					(float64(ticksDown.ticks[team][service]) + float64(ticksUp.ticks[team][service]))
			}
			score.score[team][service] = max(0, score.score[team][service])
			totalScore.score[team] += score.score[team][service] * sla.score[team][service]
		}
	}

	ticksDown.RUnlock()
	ticksUp.RUnlock()
	sla.Unlock()
	score.Unlock()
	totalScore.Unlock()
}
