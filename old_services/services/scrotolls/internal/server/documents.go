package server

import (
	"context"
	"encoding/json"
	"fmt"
	"github.com/HackerDom/ructfe2020/internal/document"
	"github.com/HackerDom/ructfe2020/internal/hashutil"
	"github.com/HackerDom/ructfe2020/internal/manager"
	httprpc "github.com/HackerDom/ructfe2020/pkg/httprtc"
	pb "github.com/HackerDom/ructfe2020/proto"
	"github.com/go-chi/chi"
	"github.com/golang/protobuf/proto"
	"io/ioutil"
	"net/http"
)

func NewDocuments(m *manager.Manager) *documentsService {
	return &documentsService{m: m}
}

type documentsService struct {
	m *manager.Manager
}

func (s *documentsService) Mount(mux *chi.Mux) {
	httprpc.New("POST", "/api/docs/create").
		Mount(mux).
		WithJSONPbReader(&pb.CreateDocumentRequest{}).
		WithJSONPbWriter().
		WithHandler(func(ctx context.Context, req proto.Message) (proto.Message, error) {
			return s.Create(ctx, req.(*pb.CreateDocumentRequest))
		})
	httprpc.New("POST", "/api/docs/list").
		Mount(mux).
		WithJSONPbReader(&pb.ListDocumentsRequest{}).
		WithJSONPbWriter().
		WithHandler(func(ctx context.Context, req proto.Message) (proto.Message, error) {
			return s.List(ctx, req.(*pb.ListDocumentsRequest))
		})
	httprpc.New("POST", "/api/docs/execute").
		Mount(mux).
		WithRequestReader(ExecuteDocumentsRequestReader).
		WithJSONPbWriter().
		WithHandler(func(ctx context.Context, req proto.Message) (proto.Message, error) {
			return s.Execute(ctx, req.(*pb.ExecuteRequest))
		})
	httprpc.New("POST", "/api/docs/test").
		Mount(mux).
		WithRequestReader(TestDocumentRequestReader).
		WithJSONPbWriter().
		WithHandler(func(ctx context.Context, req proto.Message) (proto.Message, error) {
			return s.Test(ctx, req.(*pb.TestDocRequest))
		})
}

func ExecuteDocumentsRequestReader(r *http.Request) (proto.Message, error) {
	body := struct {
		DocId int    `json:"doc_id"`
		Token string `json:"token"`
	}{}
	bodyBytes, err := ioutil.ReadAll(r.Body)
	if err != nil {
		fmt.Println(fmt.Sprintf("failed to read execute doc req: %s", err))
		return nil, err
	}
	if err := json.Unmarshal(bodyBytes, &body); err != nil {
		fmt.Println(fmt.Sprintf("failed to unmarshal execute doc req: %s", err))
		return nil, err
	}
	session, err := r.Cookie("session")
	if err != nil {
		fmt.Println(fmt.Sprintf("failed to get session: %s", err))
		return nil, err
	}
	return &pb.ExecuteRequest{
		Session: session.Value,
		DocId:   int64(body.DocId),
		Token:   body.Token,
	}, nil
}

func TestDocumentRequestReader(r *http.Request) (proto.Message, error) {
	body := struct {
		Content string `json:"content"`
	}{}
	bodyBytes, err := ioutil.ReadAll(r.Body)
	if err != nil {
		fmt.Println(fmt.Sprintf("failed to read test doc req: %s", err))
		return nil, err
	}
	if err := json.Unmarshal(bodyBytes, &body); err != nil {
		fmt.Println(fmt.Sprintf("failed to unmarshal test doc req: %s", err))
		return nil, err
	}
	session, err := r.Cookie("session")
	if err != nil {
		fmt.Println(fmt.Sprintf("failed to get session: %s", err))
		return nil, err
	}
	return &pb.TestDocRequest{
		Session: session.Value,
		Content: body.Content,
	}, nil
}

const (
	maxLimit  = 3000
	minLimit  = 1
	minOffset = 0
)

func (s *documentsService) List(ctx context.Context, req *pb.ListDocumentsRequest) (*pb.ListDocumentsResponse, error) {
	ctx, cancel := context.WithTimeout(ctx, reqTimeout)
	defer cancel()
	if err := pagingValid(req.Limit, req.Offset); err != nil {
		return nil, err
	}
	docs, err := s.m.List(ctx, int(req.Limit), int(req.Offset))
	if err != nil {
		return nil, err
	}
	return &pb.ListDocumentsResponse{Docs: docs}, nil
}

func (s *documentsService) Create(ctx context.Context, req *pb.CreateDocumentRequest) (*pb.CreateDocumentResponse, error) {
	ctx, cancel := context.WithTimeout(ctx, reqTimeout)
	defer cancel()
	d, err := document.Parse(req.Name, []byte(req.Doc))
	if err != nil {
		return nil, err
	}
	p := d.Proto()
	p.Token = hashutil.RandDigest(req.Name)
	id, err := s.m.Create(ctx, p)
	if err != nil {
		return nil, err
	}
	return &pb.CreateDocumentResponse{
		Id:    id,
		Token: p.Token,
	}, nil
}

func (s *documentsService) Execute(ctx context.Context, req *pb.ExecuteRequest) (*pb.ExecuteResponse, error) {
	ctx, cancel := context.WithTimeout(ctx, reqTimeout)
	defer cancel()
	username, err := s.m.Username(ctx, req.Session)
	if err != nil {
		return nil, err
	}
	executed, err := s.m.ExecForUser(ctx, req.DocId, username)
	if err != nil {
		return nil, err
	}
	return &pb.ExecuteResponse{Executed: executed}, nil
}

func (s *documentsService) Test(ctx context.Context, req *pb.TestDocRequest) (*pb.TestDocResponse, error) {
	ctx, cancel := context.WithTimeout(ctx, reqTimeout)
	defer cancel()
	username, err := s.m.Username(ctx, req.Session)
	if err != nil {
		return nil, err
	}
	executed, err := s.m.TestForUser(ctx, req.Content, username)
	if err != nil {
		return nil, err
	}
	return &pb.TestDocResponse{Executed: executed}, nil
}
