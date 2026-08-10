"""Tests for the standard library (``gestate/prelude.ges``).

Each test compiles a minimal program that exercises one prelude function
and verifies its result through ``evaluate()``.
"""

from __future__ import annotations

from gestate.pipeline import evaluate


def _eval(source: str) -> str:
    return evaluate(source, prelude=True)


# ── Function utilities ────────────────────────────────────────────────────────


def test_id():
    assert _eval("main : Int\nmain = id 5\n") == "5"


def test_const():
    assert _eval("main : Int\nmain = const 1 2\n") == "1"


def test_flip():
    assert _eval("main : Int\nmain = flip const 1 2\n") == "2"


def test_compose():
    # (inc @ dub) 3  =  (3 * 2) + 1  =  7 — it reads right to left.
    assert _eval("""inc : Int -> Int
inc x = x + 1

dub : Int -> Int
dub x = x * 2

main : Int
main = (inc @ dub) 3
""") == "7"


def test_compose_chains():
    """Three of them, applied right to left: ((10 - 3) * 2) + 1."""
    assert _eval("""inc : Int -> Int
inc x = x + 1

dub : Int -> Int
dub x = x * 2

sub : Int -> Int
sub x = x - 3

main : Int
main = (inc @ dub @ sub) 10
""") == "15"


def test_compose_binds_tighter_than_the_operator_beside_it():
    """9 is the point of the fixity; the associativity is unobservable.

    Composition is associative, so `infixr` against `infixl` cannot show
    up in an answer.  What can is the precedence: at 9 this is a list of
    two functions, and at anything below `::`'s 5 it is `inc` composed
    with a list, which does not typecheck.
    """
    assert _eval("""inc : Int -> Int
inc x = x + 1

dub : Int -> Int
dub x = x * 2

main : Int
main = length (inc @ dub :: dub @ inc :: [])
""") == "2"


# ── List operations ───────────────────────────────────────────────────────────


def test_map():
    # map (+1) [1,2,3] = [2,3,4]; sum = 9
    assert _eval("""inc : Int -> Int
inc x = x + 1

main : Int
main = foldr (x y => x + y) 0 (map inc [1, 2, 3])
""") == "9"


def test_foldr():
    assert _eval("""main : Int
main = foldr (x y => x + y) 0 [1, 2, 3, 4]
""") == "10"


def test_foldl():
    assert _eval("""main : Int
main = foldl (x y => x + y) 0 [1, 2, 3]
""") == "6"


def test_append():
    # `append` is below `internal` now: `++` is its public face, and the
    # `Semigroup (List b)` instance is the one line that calls it.
    assert _eval("""main : Int
main = length ([1, 2] ++ [3, 4])
""") == "4"


def test_zip_at_a_list_stops_with_the_shorter_one():
    assert _eval("""main : String
main = show (zip (x y => x + y) [1, 2, 3] [10, 20])
""") == "[11, 22]"


def test_the_note_mark_is_pure_at_whatever_the_context_asks_for():
    """`(\') : (Monad m) => a -> m a`, so it is not the score\'s alone."""
    assert _eval("""main : String
main = show ('5 : List Int)
""") == "[5]"
    assert _eval("""main : String
main = show ('7 : Maybe Int)
""") == "Just 7"


def test_concat():
    # length (join [[1],[2,3],[4]]) = 1+2+1 = 4
    assert _eval("""main : Int
main = length (join [[1], [2, 3], [4]])
""") == "4"


def test_reverse():
    # head (reverse [4,3,2,1]) = 1? No — reverse [4,3,2,1] = [1,2,3,4], head = 1
    assert _eval("""main : Int
main = case reverse [4, 3, 2, 1] of
    x :: xs -> x
    [] -> 99
""") == "1"


def test_reverse_is_a_class_so_the_score_can_have_it_too():
    """`class Reversible t` — `music.ges` instantiates it at `Score`, where
    the same word means retrograde."""
    assert _eval("""main : String
main = show (reverse [1, 2, 3])
""") == "[3, 2, 1]"


def test_ceil():
    for arg, want in [("2.5", "3"), ("(0.0 - 2.5)", "-2"), ("3.0", "3"),
                      ("(0.0 - 3.0)", "-3"), ("0.1", "1"),
                      ("(0.0 - 0.1)", "0")]:
        got = _eval(f"main : Int\nmain = ceil {arg}\n")
        assert got == want, f"ceil {arg} gave {got}"


def test_ceil_and_floor_agree_where_they_must():
    """Equal at an integral value, one apart everywhere else."""
    assert _eval("""main : String
main = show (map (x => ceil x - floor x) [2.5, 3.0, 0.1, 0.0])
""") == "[1, 0, 1, 0]"


def test_length():
    assert _eval("""main : Int
main = length [10, 20, 30, 40, 50]
""") == "5"


def test_filter():
    # filter (< 3) [1,2,3,4] = [1,2]; sum = 3
    assert _eval("""small : Int -> Bool
small n = case n < 3 of
    True -> True
    False -> False

main : Int
main = foldr (x y => x + y) 0 (filter small [1, 2, 3, 4])
""") == "3"

def test_several_prelude_functions_with_named_helpers():
    """Chain map, filter, foldr, and length through top-level helpers."""
    assert _eval("""inc : Int -> Int
inc x = x + 1

small : Int -> Bool
small n = case n < 5 of
    True -> True
    False -> False

main : Int
main = length (filter small (map inc [1, 2, 3, 4, 5]))
""") == "3"


def test_filter_empty_result():
    # filter (const False) anything = []
    assert _eval("""main : Int
main = case filter (x => False) [1, 2, 3] of
    [] -> 42
    x :: xs -> 0
""") == "42"


# ── Boolean ───────────────────────────────────────────────────────────────────


def test_not_true():
    assert _eval("""main : Int
main = case not True of
    True -> 1
    False -> 0
""") == "0"


def test_not_false():
    assert _eval("""main : Int
main = case not False of
    True -> 1
    False -> 0
""") == "1"


# ── Span preservation ─────────────────────────────────────────────────────────


def test_span_preservation():
    """A syntax error in user code reports the correct (original) line number.

    With the dual-parse prelude, line 4 of the user source must be
    reported as line 4, not shifted by the prelude's line count.
    """
    from gestate.pipeline import compile
    from gestate.syntax.parse import ParseError
    import pytest

    with pytest.raises(ParseError) as exc_info:
        compile(
            "main : Int\n\n\n\nmain =   \n",
            prelude=True,
        )
    # Pos.line is 0-based — we expect line index 4 (the 5th line).
    assert exc_info.value.pos.line == 4


# ── Integration ───────────────────────────────────────────────────────────────


def test_prelude_does_not_pollute_global_env():
    """A program compiled without prelude must not see prelude names."""
    from gestate.pipeline import compile, InferError
    import pytest

    with pytest.raises(InferError, match="foldr"):
        compile("main : Int\nmain = foldr (x y => x + y) 0 [1,2,3]\n",
                prelude=False)


def test_several_prelude_functions_together():
    """Chain map, filter, foldr, and length."""
    assert _eval("""inc : Int -> Int
inc x = x + 1

main : Int
main = length (filter (n => case n < 5 of
    True -> True
    False -> False
) (map inc [1, 2, 3, 4, 5]))
""") == "3"


# ── Shadowing ─────────────────────────────────────────────────────────────────
#
# A user definition of a prelude name wins, as a module-level definition wins
# over an implicit `Prelude` import in Haskell.  The prelude's binding is
# renamed rather than dropped, so prelude code keeps its own meaning.


def test_user_definition_shadows_the_prelude():
    assert _eval("""map : Int -> Int
map x = x + 1

main : Int
main = map 5
""") == "6"


def test_shadowing_does_not_change_other_prelude_functions():
    """`join` reaches `append`; redefining `append` must not rewire it.

    Through `Monad List`'s `>>=` now rather than directly — `join` is
    `xss >>= (xs => xs)` — so this also checks that a *class method* in the
    prelude resolves to the prelude's own `append` and not the user's.
    """
    assert _eval("""append : Int -> Int -> Int
append x y = x * y

main : Int
main = append 3 4 + length (join [[1], [2, 3]])
""") == "15"


def test_the_papers_frp_map_can_be_written():
    """Rizzo §2.4's `map` shares its name with the prelude's list `map`."""
    assert _eval("""map : (a -> b) -> Sig a -> Sig b
map f (x ::: xs) = f x ::: (map f |> xs)

main : Int
main = head (map (n => n + 1) (5 ::: never))
""") == "6"


def test_a_user_signature_alone_claims_the_name():
    assert _eval("""map : Int -> Int
map x = x * 2

main : Int
main = map 21
""") == "42"


def test_unshadowed_prelude_names_still_resolve():
    assert _eval("main : Int\nmain = length (map (x => x) [1, 2, 3])\n") == "3"


# ── Duplicate declarations ───────────────────────────────────────────────────


def test_non_adjacent_equations_are_rejected():
    from gestate.declarations import DeclError
    import pytest

    with pytest.raises(DeclError, match="Multiple declarations of 'f'"):
        _eval("""f : Int -> Int
f x = x

g : Int -> Int
g x = x

f x = x + 1

main : Int
main = f 1
""")


def test_duplicate_signature_is_rejected():
    from gestate.declarations import DeclError
    import pytest

    with pytest.raises(DeclError, match="Duplicate type signature"):
        _eval("f : Int -> Int\nf : Int -> Int\nf x = x\n\nmain : Int\nmain = f 1\n")


# ── Shadowing a *library*, not the prelude ──────────────────────────────────
#
# `prelude.ges` is merged as a module, so `merge` has always renamed a name
# the user took.  The audio libraries are concatenated as **text** by
# `audio.assemble`, so they had no such protection — and a composition with
# a `chorus` section in it collided with `synth.ges`'s chorus effect and
# would not compile at all.  `examples/audio/quartet.ges` is that program.


def test_a_library_name_the_program_takes_is_renamed_out_of_the_way():
    from gestate.prelude import library_shadowed_name, shadow_libraries

    library = "chorus : Float -> Float\nchorus x = x + 1.0\n"
    moved = shadow_libraries(library, "chorus : Int\nchorus = 3\n")
    assert library_shadowed_name("chorus") in moved
    assert "\nchorus " not in moved and not moved.startswith("chorus ")


def test_library_code_keeps_calling_its_own_definition():
    """**The reason this renames rather than drops.**  Simply letting the
    program's definition win would repoint every *library* call at it."""
    from gestate.prelude import library_shadowed_name, shadow_libraries

    library = ("chorus : Float -> Float\nchorus x = x + 1.0\n"
               "\nwiden : Float -> Float\nwiden x = chorus x * 2.0\n")
    moved = shadow_libraries(library, "chorus : Int\nchorus = 3\n")
    assert f"widen x = {library_shadowed_name('chorus')} x" in moved


def test_nothing_moves_when_nothing_collides():
    """The common case, and it has to cost nothing and change nothing."""
    from gestate.prelude import shadow_libraries

    library = "chorus : Float -> Float\nchorus x = x + 1.0\n"
    assert shadow_libraries(library, "other : Int\nother = 1\n") == library


def test_a_library_constructor_the_program_takes_is_renamed_too():
    """Types and constructors shadow by the same rule as identifiers.

    Left alone, two constructors wear one name and whichever the cons
    table keeps wins silently — the way an author's `Note := Note Int`
    broke `Score`'s `Monad` instance with `unknown global '>>='` at
    performance time, naming neither the collision nor the file.
    """
    from gestate.prelude import library_shadowed_con, shadow_libraries

    library = ("Wave a := Note a | Hush\n\n"
               "hum : Wave Int -> Int\n"
               "hum w = case w of\n"
               "    Note x -> x\n"
               "    Hush -> 0\n")
    moved = shadow_libraries(library, "Note := Note Int\n")
    assert library_shadowed_con("Note") in moved
    assert "| Note" not in moved and ":= Note" not in moved
    # The case arm follows its constructor; the untouched one stays.
    assert f"    {library_shadowed_con('Note')} x -> x" in moved
    assert "Hush -> 0" in moved


def test_a_shadowed_type_name_moves_out_of_library_signatures():
    from gestate.prelude import library_shadowed_con, shadow_libraries

    library = ("Wave a := Ping a\n\n"
               "hum : Wave Int -> Wave Int\nhum w = w\n")
    moved = shadow_libraries(library, "Wave := Wave Float\n")
    assert f"hum : {library_shadowed_con('Wave')} Int" in moved
    assert "Ping" in moved                      # not shadowed, not moved


def test_only_real_identifiers_move():
    """Driven by the tokenizer rather than by a pattern, so a name in a
    comment or a string literal is not an identifier and is left alone."""
    from gestate.prelude import shadow_libraries

    library = ("#: a chorus is an effect\n"
               "chorus : Float -> Float\nchorus x = x\n"
               "\nlabel : String\nlabel = \"chorus\"\n")
    moved = shadow_libraries(library, "chorus : Int\nchorus = 3\n")
    assert "#: a chorus is an effect" in moved, "it edited a comment"
    assert 'label = "chorus"' in moved, "it edited a string literal"


def test_a_program_redefining_clamp_does_not_rewire_the_synth_library():
    """**The failure this exists to prevent, end to end.**

    `synth.ges` calls `clamp` in filter cutoffs, the nyquist limit and
    `echo`'s feedback.  Dropping the library's copy instead of renaming it
    would silently point all of those at the program's — no error, no
    warning, wrong sound.  So the two renders have to be identical.
    """
    from gestate.audio import render

    impulse = ("trig : Sig Float\ntrig = map imp ticks\n"
               "imp : Int -> Float\nimp n = case n == 5 of\n"
               "    True -> 1.0\n    False -> 0.0\n")
    body = "sound : Sig Float\nsound = echo 0.005 0.7 trig\n"
    mine = ("clamp : Float -> Float -> Float -> Float\nclamp a b x = 0.0\n\n"
            + impulse + body)

    plain = list(render(impulse + body, 0.05, 8000))
    assert [x for x in plain if x != 0.0], "the echo was silent to begin with"
    assert list(render(mine, 0.05, 8000)) == plain
