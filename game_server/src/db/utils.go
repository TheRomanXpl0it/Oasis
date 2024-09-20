package db

import (
	"context"
	"database/sql"
	"log"
	"strconv"
	"time"

	"github.com/uptrace/bun"
	"github.com/uptrace/bun/dialect/pgdialect"
	"github.com/uptrace/bun/driver/pgdriver"
)

func ConnectDB() *bun.DB {
	sqldb := sql.OpenDB(pgdriver.NewConnector(pgdriver.WithDSN("postgres://oasis:oasis@database:5432/oasis?sslmode=disable")))
	if sqldb == nil {
		panic("failed to connect to database")
	}
	db := bun.NewDB(sqldb, pgdialect.New())
	return db
}

func GetStartTime() time.Time {
	db := ConnectDB()
	ctx := context.Background()
	defer db.Close()

	envVar := new(Environment)

	if err := db.NewSelect().Model(envVar).Where("key = ?", "START_TIME").Scan(ctx); err != nil {
		if err == sql.ErrNoRows {
			nowTime := time.Now().UTC()
			_, err := db.NewInsert().Model(&Environment{
				Key:   "START_TIME",
				Value: nowTime.Format(time.RFC3339),
			}).Exec(context.Background())
			if err != nil {
				log.Panicf("Error inserting start time: %v", err)
			}
			return nowTime
		} else {
			log.Panicf("Error fetching start time: %v", err)
		}
	}
	startTime, err := time.Parse(time.RFC3339, envVar.Value)
	if err != nil {
		log.Panicf("Error parsing start time: %v", err)
	}
	return startTime
}

func GetExposedRound() int {
	db := ConnectDB()
	ctx := context.Background()
	defer db.Close()

	envVar := new(Environment)

	if err := db.NewSelect().Model(envVar).Where("key = ?", "ACTUAL_ROUND_EXPOSED").Scan(ctx); err != nil {
		if err == sql.ErrNoRows {
			_, err := db.NewInsert().Model(&Environment{
				Key:   "ACTUAL_ROUND_EXPOSED",
				Value: "-1",
			}).Exec(context.Background())
			if err != nil {
				log.Panicf("Error inserting exposed round: %v", err)
			}
			return -1
		} else {
			log.Panicf("Error fetching exposed round: %v", err)
		}
	}
	exposedRound, err := strconv.Atoi(envVar.Value)
	if err != nil {
		log.Panicf("Error parsing exposed round time: %v", err)
	}
	return exposedRound
}

func SetExposedRound(round int64) {
	db := ConnectDB()
	ctx := context.Background()
	defer db.Close()

	envVar := new(Environment)

	_, err := db.NewUpdate().Model(envVar).Set("value = ?", round).Where("key = ?", "ACTUAL_ROUND_EXPOSED").Exec(ctx)
	if err != nil {
		log.Panicf("Error updating exposed round: %v", err)
	}
}

func InitDB() {
	db := ConnectDB()
	defer db.Close()

	ctx := context.Background()

	models := []interface{}{
		(*Flag)(nil),
		(*FlagSubmission)(nil),
		(*StatusHistory)(nil),
		(*Environment)(nil),
		(*ServiceScore)(nil),
	}

	// Create tables
	for _, model := range models {
		if _, err := db.NewCreateTable().Model(model).IfNotExists().Exec(ctx); err != nil {
			log.Fatalf("Error creating table model: %v", err)
		}
	}

	GetExposedRound() // Ensure the exposed round is set

	_, err := db.ExecContext(ctx, `
		CREATE INDEX IF NOT EXISTS idx_flags_team ON flags(team);
		CREATE INDEX IF NOT EXISTS idx_flags_round ON flags(round);
		CREATE INDEX IF NOT EXISTS idx_flags_service ON flags(service);
		CREATE INDEX IF NOT EXISTS idx_flags_created_at ON flags(created_at);
		CREATE INDEX IF NOT EXISTS idx_flag_submissions_flag_id ON flag_submissions(flag_id);
		CREATE INDEX IF NOT EXISTS idx_flag_submissions_team ON flag_submissions(team);
		CREATE INDEX IF NOT EXISTS idx_flag_submissions_submitted_at ON flag_submissions(submitted_at);
		CREATE INDEX IF NOT EXISTS idx_sla_statues_team ON sla_statues(team);
		CREATE INDEX IF NOT EXISTS idx_sla_statues_service ON sla_statues(service);
		CREATE INDEX IF NOT EXISTS idx_sla_statues_round ON sla_statues(round);
		CREATE INDEX IF NOT EXISTS idx_service_scores_team ON service_scores(team);
		CREATE INDEX IF NOT EXISTS idx_service_scores_service ON service_scores(service);
	`)
	if err != nil {
		log.Fatalf("Error creating indexs: %v", err)
	}

}
