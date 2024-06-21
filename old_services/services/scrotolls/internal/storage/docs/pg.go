package docs

import (
	"context"
	"fmt"
	pb "github.com/HackerDom/ructfe2020/proto"
	"github.com/jmoiron/sqlx"
	"go.uber.org/zap"
	"google.golang.org/protobuf/proto"
)

type Documents interface {
	List(ctx context.Context, limit, offset int) ([]*pb.Document, error)
	Insert(ctx context.Context, document *pb.Document) (int64, error)
	Delete(ctx context.Context, docID int64) error
	Get(ctx context.Context, name int64) (*pb.Document, error)
}

var docsSchema = `CREATE TABLE IF NOT EXISTS documents (
	id 						SERIAL PRIMARY KEY,
    content					BYTEA NOT NULL
);`

type doc struct {
	Id      int    `db:"id"`
	Content []byte `db:"content"`
}

func (d *doc) Proto() (*pb.Document, error) {
	p := &pb.Document{}
	err := proto.Unmarshal(d.Content, p)
	if err != nil {
		return nil, err
	}
	p.Id = int64(d.Id)
	return p, nil
}

func NewPg(db *sqlx.DB, l *zap.Logger) (Documents, error) {
	_, err := db.Exec(docsSchema)
	if err != nil {
		return nil, err
	}
	return &pg{db: db, l: l}, nil
}

type pg struct {
	db *sqlx.DB
	l  *zap.Logger
}

func (p *pg) List(ctx context.Context, limit, offset int) ([]*pb.Document, error) {
	ds := make([]doc, 0)
	err := p.db.SelectContext(ctx, &ds, "SELECT id, content FROM documents LIMIT $1 OFFSET $2;", limit, offset)
	if err != nil {
		return nil, err
	}
	pdocs := make([]*pb.Document, len(ds))
	for i, d := range ds {
		pdocs[i], err = d.Proto()
		if err != nil {
			return nil, err
		}
	}
	return pdocs, nil
}

func (p *pg) Insert(ctx context.Context, document *pb.Document) (int64, error) {
	pr, err := proto.Marshal(document)
	if err != nil {
		return 0, err
	}
	row, err := p.db.QueryContext(ctx, "INSERT INTO documents (content) VALUES ($1) RETURNING id;", pr)
	if err != nil {
		return 0, err
	}

	id := 0
	if !row.Next() {
		return 0, fmt.Errorf("not enougth returning rows")
	}
	err = row.Scan(&id)
	return int64(id), err
}

func (p *pg) Delete(ctx context.Context, docID int64) error {
	_, err := p.db.ExecContext(ctx, "DELETE (id, content) FROM documents WHERE id = $1;", docID)
	return err
}

func (p *pg) Get(ctx context.Context, id int64) (*pb.Document, error) {
	rows, err := p.db.QueryContext(ctx, "SELECT id, content FROM documents WHERE id = $1;", id)
	if err != nil {
		return nil, err
	}
	if !rows.Next() {
		return nil, fmt.Errorf("not enougth returning rows")
	}
	d := &doc{}
	err = rows.Scan(&d.Id, &d.Content)
	if err != nil {
		return nil, err
	}
	return d.Proto()
}
