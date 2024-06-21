package eval

import (
	"github.com/HackerDom/ructfe2020/pkg/eval/funcs"
	pb "github.com/HackerDom/ructfe2020/proto"

	"github.com/google/cel-go/cel"

	"fmt"
)

func Eval(expr string, vars map[string]string, users []*pb.User) (string, error) {
	e, opts, err := createEnv(vars, users)
	if err != nil {
		return "", err
	}
	ast, iss := e.Compile(expr)
	if iss.Err() != nil {
		return "", iss.Err()
	}
	prg, err := e.Program(ast, opts...)
	if err != nil {
		return "", err
	}
	out, _, err := prg.Eval(getVarsIface(vars))
	if err != nil {
		return "", err
	}
	res, ok := out.Value().(string)
	if !ok {
		return "", fmt.Errorf("eval result should be <bool>, but was: '%v'", out.Value())
	}
	return res, nil
}

func createEnv(vars map[string]string, users []*pb.User) (*cel.Env, []cel.ProgramOption, error) {
	opts, fs := funcs.EnvOptions(vars, users)
	opts = append(opts, funcs.VarsDecls(getVarsIface(vars))...)
	env, err := cel.NewEnv(cel.Declarations(opts...))
	if err != nil {
		return nil, nil, err
	}
	return env, []cel.ProgramOption{cel.Functions(fs...)}, nil
}

func getVarsIface(vars map[string]string) map[string]interface{} {
	res := make(map[string]interface{}, len(vars))
	for k, v := range vars {
		res[k] = v
	}
	return res
}