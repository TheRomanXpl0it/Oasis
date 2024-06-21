package sessions

import (
	"context"
	"fmt"
	"github.com/jmoiron/sqlx"
	"go.uber.org/zap"
)

var tokenToUserSchema = `CREATE TABLE IF NOT EXISTS tokens (
	token					TEXT PRIMARY KEY,
	name					TEXT
);`

type Sessions interface {
	Insert(ctx context.Context, name, session string) error
	Username(ctx context.Context, session string) (string, error)
	Token(ctx context.Context, name string) (string, error)
}

func NewPg(db *sqlx.DB, l *zap.Logger) (Sessions, error) {
	_, erro := db.Exec(tokenToUserSchema)
	if erro != nil {
		return nil, erro
	}
	return &Pg{db: db, l: l}, nil
}

type Pg struct {
	db *sqlx.DB
	l  *zap.Logger
}

func (p *Pg) Insert(ctx context.Context, name, session string) error {
	_, err := p.db.ExecContext(ctx, "INSERT INTO tokens (token, name) VALUES ($1, $2);", session, name)
	if err != nil {
		return err
	}
	return nil
}

func (p *Pg) Username(ctx context.Context, session string) (string, error) {
	var names []string
	err := p.db.SelectContext(ctx, &names, "SELECT name FROM tokens WHERE token=$1", session)
	if err != nil {
		return "", err
	}
	if len(names) == 0 {
		return "", fmt.Errorf("invalid session")
	}
	return names[0], nil
}

func (p *Pg) Token(ctx context.Context, username string) (string, error) {
	var tokens []string
	err := p.db.SelectContext(ctx, &tokens, "SELECT token FROM tokens WHERE name=$1", username)
	if err != nil {
		return "", err
	}
	if len(tokens) == 0 {
		return "", fmt.Errorf("invalid username")
	}
	return tokens[0], nil
}
