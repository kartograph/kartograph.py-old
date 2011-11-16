watch ( '.*\.coffee' ) { |md| system("coffee -o js #{md[0]}") }
