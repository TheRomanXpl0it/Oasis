package funcs

import (
	pb "github.com/HackerDom/ructfe2020/proto"
	"github.com/google/cel-go/checker/decls"
	"github.com/google/cel-go/common/types"
	"github.com/google/cel-go/common/types/ref"
	"github.com/google/cel-go/interpreter/functions"
	exprpb "google.golang.org/genproto/googleapis/api/expr/v1alpha1"

	"reflect"
)

func EnvOptions(inerCtx map[string]string, users []*pb.User) (decls []*exprpb.Decl, funcs []*functions.Overload) {
	funcs, funcsDecls := make([]*functions.Overload, 0), make([]*exprpb.Decl, 0)
	funcs, funcsDecls = GetInfoFunc(inerCtx["username"], users, funcs, funcsDecls)
	return funcsDecls, funcs
}

func VarsDecls(vars map[string]interface{}) []*exprpb.Decl {
	varsDecls := make([]*exprpb.Decl, 0)
	for name, val := range vars {
		switch reflect.TypeOf(val).Kind() {
		case reflect.String:
			varsDecls = append(varsDecls, decls.NewVar(name, decls.String))
		case reflect.Slice:
			varsDecls = append(varsDecls, decls.NewVar(name, decls.NewListType(decls.String)))
		case reflect.Int:
			varsDecls = append(varsDecls, decls.NewVar(name, decls.Int))
		case reflect.Int32:
			varsDecls = append(varsDecls, decls.NewVar(name, decls.Int))
		case reflect.Int64:
			varsDecls = append(varsDecls, decls.NewVar(name, decls.Int))
		case reflect.Float64:
			varsDecls = append(varsDecls, decls.NewVar(name, decls.Double))
		default:
			varsDecls = append(varsDecls, decls.NewVar(name, decls.Dyn))
		}
	}
	return varsDecls
}

func GetInfoFunc(username string, users []*pb.User, funcs []*functions.Overload, declarations []*exprpb.Decl) ([]*functions.Overload, []*exprpb.Decl) {
	findSecret := func(username, kind string) string {
		for _, user := range users {
			if user.Name != username {
				continue
			}
			switch kind {
			case "bio":
				return user.Bio
			case "name":
				return user.Name
			}
		}
		return ""
	}
	f, d := &functions.Overload{
		Operator: "get_info_string",
		Unary: func(lhs ref.Val) ref.Val {
			greetings := lhs.Value().(string)
			return types.String(findSecret(username, greetings))
		},
	}, decls.NewFunction("get_info",
		decls.NewOverload("get_info_string",
			[]*exprpb.Type{decls.String},
			decls.String))
	return append(funcs, f), append(declarations, d)
}
