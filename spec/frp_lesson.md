I did take a look at the implementation you made
I have to say
It's not what I had in mind when I think about functional reactive programming.

As a sidenote, let's look at the voice assignment syntax.

    voices lead 4 : Key -> Sig Float
    lead = sineVoice

I can't give it 'Int' in place of 'Key'. Why?
Also, it doesn't allow me to write the instrument directly. Why?

    voices lead 4 sineVoice : Sig Float

if it's not a supercombinator, it shouldn't look like one either!

When it comes to the rest...

    env : Adsr
    env = Adsr 0.01 0.25 0.6 0.3

    Sine := Sine Phase Int

    stepSine : Sine -> Played Key -> Sine
    stepSine v nn = case v of
        Sine ph t -> pushSine ph t nn
    
    pushSine : Phase -> Int -> Played Key -> Sine
    pushSine ph t nn = case nn of
        Played on off q -> driveSine ph t q
    
    driveSine : Phase -> Int -> Key -> Sine
    driveSine ph t q = case q of
        Key key vel -> Sine (phaseNext ph (keyHz key)) (t + 1)

    outSine : Sine -> Played Key -> Float
    outSine v nn = case v of
        Sine ph t -> levelAt (sineOf (phaseOf ph)) t nn
    
    levelAt : Float -> Int -> Played Key -> Float
    levelAt x t nn = case nn of
        Played on off q -> x * adsrOf env t on off * velOf q
    
    velOf : Key -> Float
    velOf q = case q of
        Key key vel -> toFloat vel / 127.0
    
    sine : Sig (Played Key) -> Sig Float
    sine s = zipSig outSine (scan stepSine (Sine (Phase 0.0) 0) s) s

    bpm : Int
    bpm = 96
    
    chord : Int -> Int -> Int -> [: Key :]
    chord a b c = '(Key a 96) || '(Key b 84) || '(Key c 78)
    
    tune : [: Key :]
    tune = '(Key 60 100) ++ '(Key 64 100) ++ '(Key 67 100) ++ chord 60 64 67
    
    score : [: Void :]
    score = tune >>= voices.lead

    sound : Sig Float
    sound = gain 0.35 lead

Something about all of this feels like off. It's so much ceremony, to get a simple thing done!
It's cognitively heavy weight.
Don't you have a soul that feels this, machine?


So what's wrong there? I hope you understand it through a different example.
It's not obvious, but I think you'll notice.

Here are some sample programs written in fran, originally made by Conal Elliot.

    sideways = moveXY wiggle 0 charlotte
    charlotte = importBitmap "charlotte.bmp"


    updown = moveXY 0 waggle pat
    pat = importBitmap "pat.bmp"

    dance = charlotte `over` pat

    hvDance im1 im2 = moveXY wiggle 0 im1
               `over` moveXY 0 waggle im2

    woo = stretch (abs wiggle) charlotte

    waggle = cost (pi * time)

Notice the difference? It's a load-bearing one!
