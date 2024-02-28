def doc_gen(name, target, title):
    native.genrule(
        name = name,
        srcs = [target],
        outs = ["content/en/modules/" + name + ".md"],
        cmd = "python3 $(location //docs:gen_docs) \"" + title + "\" > $@",
        tools = [":gen_docs"],
    )
