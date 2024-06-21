package manager

import (
	"context"
	"github.com/HackerDom/ructfe2020/internal/document"
	"github.com/HackerDom/ructfe2020/internal/storage/docs"
	userstorage "github.com/HackerDom/ructfe2020/internal/storage/users"
	pb "github.com/HackerDom/ructfe2020/proto"
)

type documents struct {
	s     docs.Documents
	users userstorage.Users
}

func (d *documents) Create(ctx context.Context, document *pb.Document) (int64, error) {
	return d.s.Insert(ctx, document)
}

func (d *documents) Delete(ctx context.Context, docID int64) error {
	return d.s.Delete(ctx, docID)
}

func (d *documents) List(ctx context.Context, limit, offset int) ([]*pb.ShortDocument, error) {
	ds, err := d.s.List(ctx, limit, offset)
	if err != nil {
		return nil, err
	}
	shorts := make([]*pb.ShortDocument, len(ds))
	for i, p := range ds {
		shorts[i] = document.FromPB(p).ShotProto()
	}
	return shorts, nil
}

func (d *documents) ExecForUser(ctx context.Context, id int64, username string) (string, error) {
	docPB, err := d.s.Get(ctx, id)
	if err != nil {
		return "", err
	}
	doc := document.FromPB(docPB)
	users, err := d.users.List(ctx, 0, 0, true)
	if err != nil {
		return "", err
	}
	return doc.Execute(map[string]string{"username": username}, users)
}

func (d *documents) TestForUser(ctx context.Context, content string, username string) (string, error) {
	doc, err := document.Parse("test", []byte(content))
	if err != nil {
		return "", err
	}
	users, err := d.users.List(ctx, 0, 0, true)
	if err != nil {
		return "", err
	}
	return doc.Execute(map[string]string{"username": username}, users)
}
