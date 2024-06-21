package document

import (
	"bytes"
	"fmt"
	pb "github.com/HackerDom/ructfe2020/proto"

	"github.com/slongfield/pyfmt"
	"gopkg.in/yaml.v2"

	"github.com/HackerDom/ructfe2020/pkg/eval"
)

func FromPB(document *pb.Document) *Document {
	return &Document{
		name: document.Name,
		ctx:  document.Context,
		tmpl: document.Content,
		id:   document.Id,
	}
}

func Parse(name string, dcmt []byte) (*Document, error) {
	splited := bytes.Split(dcmt, []byte("\n---\n"))
	if len(splited) != 2 {
		return nil, fmt.Errorf("'\n---\n' should split doc in 2 parts")
	}
	exprsYAML := splited[0]
	tmplBytes := splited[1]
	d := &Document{
		name: name,
		tmpl: string(tmplBytes),
	}
	err := yaml.UnmarshalStrict(exprsYAML, &d.ctx)
	if err != nil {
		return nil, err
	}
	return d, nil
}

type Document struct {
	name string
	ctx  *pb.Ctx
	vars map[string]string
	tmpl string
	id   int64
}

func (d *Document) Execute(context map[string]string, users []*pb.User) (string, error) {
	err := d.prepareVars(context, users)
	if err != nil {
		return "", err
	}
	fmted, err := pyfmt.Fmt(d.tmpl, d.vars)
	if err != nil {
		return "", err
	}
	return fmted, nil
}

func (d *Document) prepareVars(context map[string]string, users []*pb.User) error {
	templVars := make(map[string]string)
	for k, v := range context {
		templVars[k] = v
	}
	for k, v := range d.ctx.Vars {
		templVars[k] = v
	}
	for _, expr := range d.ctx.Exprs {
		evaled, err := eval.Eval(expr.Expr, templVars, users)
		if err != nil {
			return err
		}
		templVars[expr.Name] = evaled
	}
	d.vars = templVars
	return nil
}

func (d *Document) Proto() *pb.Document {
	return &pb.Document{
		Id:      d.id,
		Name:    d.name,
		Context: d.ctx,
		Content: d.tmpl,
	}
}

func (d *Document) ShotProto() *pb.ShortDocument {
	return &pb.ShortDocument{
		Id:   d.id,
		Name: d.name,
	}
}