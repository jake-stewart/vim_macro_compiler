syn clear

syn match VmcStatement "\s*\zs.*"

syn match VmcAssignment "\v^\s*[a-z_]+\s*\=\s*.*"
syn match VmcStatement ".*" contained containedin=VmcAssignment
syn match VmcAssignmentHead "\v^\s*[a-z_]+\s*\=\s*" contained containedin=VmcAssignment
syn match Operator "=" contained containedin=VmcAssignmentHead

syn match VmcArgs '.*' contained containedin=VmcStatement

syn match VmcEval '\v(eval|elif|if|while)\s*.*' contained containedin=VmcStatement
syn match VmcJump '\v(goto|mark)\s*.*' contained containedin=VmcStatement
syn match Operator 'else' contained containedin=VmcStatement
syn match Function '\v(set|print|input|norm)' contained containedin=VmcStatement
syn match Type '.*' contained containedin=VmcJump
syn match Operator '\v(goto|mark)' contained containedin=VmcJump

syn region String start='"' skip='\\"' end='"' contained containedin=VmcArgs,VmcEval,Type
syn region String start="'" skip="\\'" end="'" contained containedin=VmcEval,VmcEval,Type
syn match Function '\\n' contained containedin=String

syn match Function 'eval' contained containedin=VmcEval
syn match Operator '\v(elif|if|while)' contained containedin=VmcEval
syn match Operator '[<>=!~+/*%.-]' contained containedin=VmcEval
syn match Number '\v\d+(\.\d+)?' contained containedin=VmcEval
syn match Function '\v[a-z_]+\ze\(' contained containedin=VmcEval

syn match Comment "\s*#.*"
