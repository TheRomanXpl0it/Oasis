package storage

import (
	"fmt"
	"github.com/HackerDom/ructfe2020/internal/storage/docs"
	"github.com/HackerDom/ructfe2020/internal/storage/sessions"
	"github.com/HackerDom/ructfe2020/internal/storage/users"
	_ "github.com/jackc/pgx/v4/stdlib"
	"github.com/jmoiron/sqlx"
	"go.uber.org/zap"
	"net"
	"strings"
	"time"
)

const (
	Addr = "[::]"
	Port = "2379"
)

const (
	maxOpenConn     = 10
	connMaxLifetime = time.Minute
)

// pg conn string params
const (
	dbAddr     = "postgres"
	dbUser     = "service"
	dbPassword = "service"
	dbName     = "service"
)

func Init(l *zap.Logger) (docs.Documents, users.Users, sessions.Sessions, error) {
	conn, err := CreateConnection(l)
	if err != nil {
		return nil, nil, nil, err
	}
	usersdb, err := users.NewPg(conn, l)
	if err != nil {
		return nil, nil, nil, err
	}
	docksdb, err := docs.NewPg(conn, l)
	if err != nil {
		return nil, nil, nil, err
	}
	sessdb, err := sessions.NewPg(conn, l)
	if err != nil {
		return nil, nil, nil, err
	}
	return docksdb, usersdb, sessdb, nil
}

func CreateConnection(l *zap.Logger) (*sqlx.DB, error) {
	connString := ConnString(dbAddr, dbName, dbUser, dbPassword)
	l.Info(fmt.Sprintf("Connecting to '%s'", connString))
	db, err := sqlx.Open("pgx", connString)
	if err != nil {
		return nil, err
	}
	l.Info(fmt.Sprintf("Setting MaxOpenConns to %d", maxOpenConn))
	l.Info(fmt.Sprintf("Setting ConnMaxLifetime to %s", connMaxLifetime))
	db.SetMaxOpenConns(maxOpenConn)
	db.SetConnMaxLifetime(connMaxLifetime)
	return db, nil
}

// ConnString constructs PostgreSQL connection string
func ConnString(addr, dbname, user, password string) string {
	var connParams []string
	host, port, err := net.SplitHostPort(addr)
	if err == nil {
		connParams = append(connParams, "host="+host)
		connParams = append(connParams, "port="+port)
	} else {
		connParams = append(connParams, "host="+addr)
	}
	if dbname != "" {
		connParams = append(connParams, "dbname="+dbname)
	}
	if user != "" {
		connParams = append(connParams, "user="+user)
	}
	if password != "" {
		connParams = append(connParams, "password="+password)
	}
	connParams = append(connParams, "sslmode="+"disable")
	return strings.Join(connParams, " ")
}
