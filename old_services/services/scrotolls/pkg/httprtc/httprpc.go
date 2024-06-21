package httprpc

import (
	"github.com/HackerDom/ructfe2020/pkg/httputil"

	"github.com/go-chi/chi"
	"github.com/golang/protobuf/proto"
	"github.com/rs/cors"
	"google.golang.org/protobuf/encoding/protojson"

	"context"
	"io/ioutil"
	"log"
	"net/http"
	"strconv"
)

func New(method, path string) *RPC {
	return &RPC{
		l:      log.New(ioutil.Discard, "", 0),
		method: method,
		path:   path,
	}
}

type Handler func(ctx context.Context, req proto.Message) (proto.Message, error)
type reader func(*http.Request) (proto.Message, error)
type writer func(http.ResponseWriter, proto.Message) error

type RPC struct {
	l *log.Logger

	r         reader
	h         Handler
	w         writer
	errWriter writer

	cors   *cors.Cors
	method string
	path   string
}

func (r *RPC) WithLogger(l *log.Logger) *RPC {
	r.l = l
	return r
}

func (r *RPC) CorsAllowAll() *RPC {
	r.cors = cors.AllowAll()
	return r
}

func (r *RPC) WithHandler(h Handler) *RPC {
	r.h = h
	return r
}

// Unmarshalling json as protobuf message
// If parsing failed returns http error 400
func (r *RPC) WithJSONPbReader(p proto.Message) *RPC {
	r.r = func(req *http.Request) (proto.Message, error) {
		content, err := ioutil.ReadAll(req.Body)
		if err != nil {
			return nil, err
		}
		err = protojson.Unmarshal(content, proto.MessageV2(p))
		if err != nil {
			return nil, err
		}
		return p, nil
	}
	return r
}

// Custom request to protobuf transformation function
// If parsing failed returns http error 400
func (r *RPC) WithRequestReader(re reader) *RPC {
	r.r = re
	return r
}

var mrshlr = protojson.MarshalOptions{
	Multiline:       true,
	Indent:          "  ",
	EmitUnpopulated: true,
}

func (r *RPC) WithJSONPbWriter() *RPC {
	r.w = func(w http.ResponseWriter, respPb proto.Message) error {
		w.Header().Set(string(httputil.HeaderContentType), string(httputil.TypeApplicationJSON))
		mrshld, err := mrshlr.Marshal(proto.MessageV2(respPb))
		if err != nil {
			return err
		}
		_, err = w.Write(mrshld)
		return err
	}
	return r
}
func (r *RPC) WithCustomWriter(wr func(w http.ResponseWriter, respPb proto.Message) error) *RPC {
	r.w = wr
	return r
}

func (r *RPC) Mount(mux *chi.Mux) *RPC {
	httpHandler := http.HandlerFunc(func(w http.ResponseWriter, request *http.Request) {
		if r.cors != nil {
			r.cors.HandlerFunc(w, request)
		}
		req, err := r.r(request)
		// we fail on reading transforming request -> pb
		// often means we can not marshal json -> pb,
		// may be some fields are invalid
		if err != nil {
			fail(err, w, http.StatusBadRequest)
			return
		}
		res, err := r.h(request.Context(), req)
		if err != nil {
			fail(err, w, http.StatusInternalServerError)
			return
		}
		err = r.w(w, res)
		if err != nil {
			fail(err, w, http.StatusInternalServerError)
		}
	})
	mux.Method(r.method, r.path, httpHandler)
	return r
}

func fail(err error, w http.ResponseWriter, statusCode int) {
	w.WriteHeader(statusCode)
	resp := []byte(err.Error())
	w.Header().Set(string(httputil.HeaderContentType), string(httputil.TypeTextPlain))
	w.Header().Set(string(httputil.HeaderContentLength), strconv.Itoa(len(resp)))
	_, _ = w.Write(resp)
}
