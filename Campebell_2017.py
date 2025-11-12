https://www.youtube.com/watch?v=x5V2nvxco90

Introduction
as you just said a man Campbell and I'm
here today to talk about cognitive
complexity cognitive complexity is a new
metric that was released by centre
source in December I am the principal
author but I had plenty of help from my
colleagues and among those was Freddie
male jean-christophe Kalle and Nicola
tell who you might guess they're all
French cognitive complexity is available
today as a rule in the mainstream center
analyzers so that's jealousy sharp
JavaScript PHP etc by the end of the
year we hope to have it available as a
rule in all of the center cube analyzers
it's available in the next version of
seminar Java as a metric and we're going
to be looking at both of those today and
again by the end of the year we hope to
have it available as a metric in all of
the analyzers its laid out in a white
paper that was released initially in
December it's already been through a
couple of versions here's the URL you
guys have access to the slides and you
know we put this metric out but we're
hoping that other people will adopt it
so feel free to implement it on your own
inside or outside of a sooner cube
plugin now when most people think about
complexity they go to cyclomatic
complexity that's been the gold standard
for the last forty years or so but two
Cyclomatic Complexity
things about cyclomatic complexity or
widely acknowledged the first is that
it's absolutely spot-on for testability
the cyclomatic complexity score of a
method is exactly the minimum number of
test cases you need to fully unit test
that method but it's also widely
acknowledged that on maintainability it
missed the mark and as an example I've
got these two methods on the Left I've
Example
got get words which is a method that
consists of a single switch with a few
cases and a default and that's it and
that gets a cyclomatic complexity of
four and on the right I've got some of
primes which is a little bit more
complicated so we've got a for loop and
inside that another for loop and inside
that an if statement and then we've got
a jump to a label and because there are
four paths through each of these pieces
of code they get equal cycle
maduk complexity scores but obviously
they're not equally understandable and
that's where cognitive complexity comes
in so there are two motivations behind
Motivations
cognitive complexity the first is
obviously to measure understand ability
the second is to incent good code when I
was formulating cognitive complexity I
was very aware of the fact that if I
measure it
someone somewhere is going to try and
get a better score by eliminating it so
that leads us straight into the first
guiding principle of cognitive
Ignore readable shorthand structures
complexity which is to ignore readable
shorthand structures now what I mean by
readable shorthand structures are
specifically the method structure itself
cyclomatic complexity increments one
every time you have just a plain old
method that means that a domain class
with let's say 30 members is going to
have 60 methods and instantly without
any logic in it class isn't doing
anything
you've got a cyclomatic complexity of 60
now the other thing about this is that
if I've got a method would say 100 lines
and I want to excerpt 10 of those into a
readable named other method when I want
to shorthand those 10 method 10 lines
into another method if I'm incrementing
for the method structure then that's a
disincentive to do that cleanup behavior
right so that's why we're going to
ignore the method structure itself
there's no increment for the method the
other thing we're going to ignore is the
null coalescing operators that you find
in languages like C sharp
I think PHP may be swift several
languages have these here's an example
both of these pieces of code do exactly
the same thing the code on the Left
takes a minute to read through you have
to read through this to understand
what's going on once you understand the
null coalescing syntax the code on the
right is instantly understandable takes
no effort at all and so that's why we're
going to ignore null coalescing
operators what we don't ignore is breaks
Breaking linear flow
in the linear flow the theory here is
that ideally you would be able to read
code like you read a novel left-to-right
top
bottom in an unbroken flow but of course
code doesn't work that way because we
have these control flow structures that
move the flow around so we're going to
increment for that and specifically
Increments
these are the structures that we
increment for so if else if else the
ternary operator there's a single
increment for a switch and all its cases
there's a single increment for a catch
no matter how many exception types it's
catching there's an increment for each
kind of loop so that's four for each
while do-while etc we're going to
increment for sequences of logical
operators now this diverges from what
you're used to with cyclomatic
complexity because cyclomatic complexity
increments once for each operator but
the fact is that a and B and C it's not
that much harder to understand than a
and B and that's what we're after is
measuring how hard it is to understand
right so for a sequence of same logical
operators like we're going to increment
once on the other hand when you get to a
and B or C and D that's a little bit
harder to understand so once the
operator starts switching up then we
increment for each time it switches okay
the other thing we increment for is
jumps to labels so obviously that's goto
but also break to a label and continue
to a label because those make the flow
go in some odd direction that you have
to figure out and finally for a
recursion there are two reasons we
increment for recursion one is that
recursion is a loop and we increment for
loops and the other is that I've seen
some even seasoned programmers blanch at
the thought of dealing with recursion
that means recursion is hard and that's
what we're trying to measure so we
increment for it we're going to
increment once for each method in a
recursion cycle so direct recursion is
+1 a recursion cycle of two methods
would be +1 on each method the other
Nesting
thing we increment for is nesting
commensurate with the level of nesting
all right these are the structures oh
come on
these are the structures that both
increment the nesting level and receive
a nesting increment so loops switches
caches if and turnery notice what I've
left out there I've left out else if and
Nested Methods
else because you're not ever going to
have an else--if without and if and
you've already paid the nesting penalty
when you dealt with the if both mentally
and in cognitive complexity however else
if and else do increment the nesting
level so that if I have a while inside
an else if we are going to pay attention
to the fact that it's nested the other
thing that increments the nesting level
without receiving a nesting increment is
a nested method or lambda that sort of
structure and you can find those that
kind of thing in a lot of languages
again there's no increment for the
method itself but when you have one
method inside another it's a little bit
harder to understand so we're going to
pay attention to that in cognitive
complexity by upping the nesting level
this will make a little more sense once
we start looking at actual code which I
promise we're going to do soon but first
I want to come back to my example
methods all right so get words on the
Single Methods
left again is a single method consisting
of a switch with a few cases in a
default now because cognitive complexity
doesn't increment for the method itself
there's no increment there we increment
once for the switch and all its cases
and so this method gets a cognitive
complexity of one on the other hand
we've got some of primes which starts
with a for loop that's plus one for the
four inside that is another for loop
Primes
that's plus one for the four and plus
one for the nesting inside that is an if
so that's plus one for the if plus 2 for
the nesting then we've got our jump to a
label we increment once for the jump to
the label there's no nesting penalty on
this jump and that gives us a total
cognitive complexity of seven so now if
we're looking at just the numbers and
not the code we understand instantly
which piece of code is going to be more
difficult to understand and therefore to
maintain properly
all right so let's look at some more
real life code I'm going to start yeah
didn't reset my legs here all right so
right now I'm on next sonarqube comm
SonarQube
which is our internal dogfooding
instance of center cube and this is open
to the public not all of the projects
are you guys won't be able to get to
this project but you can come to this
instance and see what we're working on
and I'm picking on this particular
closed source project because I wrote
because I wrote most of the code so I
can pick on it ruthlessly and not hurt
anyone's feelings but my own all right
Cognitive Complexity
so I'm going to drill into the measures
here and go down to the complexity and
the first thing I want to point out is
this 17:24 this is the total cyclomatic
complexity of the application on the
other hand cognitive complexity in a
somewhat smaller font is a total of 12
59 so already we see a divergence there
let's look at where that might be coming
from so I'm going to drill in and go to
the package view and can you guys see
this okay okay all right that's a little
bit better all right so the first thing
I want to point out is that because
there's no increment for the method
structure itself it's now possible to
have methods with a zero complexity and
therefore classes with a zero complexity
and therefore packages with a zero
complexity like we've got down here at
the bottom in this misery probe to you
that it's not an empty package I'm going
to click through and show you it's got
three classes in it and to prove to you
that these are non-empty classes I'm
going to show you one of them it's
pretty ugly first we've got this
enormous really ugly enum no complexity
here no logic and then about three days
later we come down to basically some
domain some getters and setters right
there's no logic here with plenty of
lines of code but there's no logic and
that's why we get a zero cognitive
complexity
again alright so come back up here and
it's the same story with these other two
classes I'm not going to bore you by
showing them til you they look almost
exactly the same coming back up to the
tree level there we go so again it's
possible now to have packages with a
zero complexity so that you can look at
it look at the application at this level
and know where your logic hotspots are
so let's take a little bit closer look
and here I've got this domain class one
would reasonably expect a domain package
to have a cognitive complexity of zero
at or near that the fact that it's in
the middle of the list here is kind of
suspicious so let's see what's going on
here
in the domain package we do actually
have a couple of classes with zero
complexity and again they're non-empty
but here at the top we've got this rural
comparison class with a complexity of 75
which you might think is a bit high for
a domain class and if we look inside
yeah we've got a lot of logic here so
maybe this class doesn't actually belong
in a package names domain
maybe it just needs to be moved
somewhere else maybe it needs to be
rethought but I'll point out to you
there are zero issues in this and it'll
become a little bit more obvious in a
minute why this is significant but
because there are zero issues I know
offhand that there's no single method in
this class with a too high cognitive
complexity so the class itself is maybe
structured okay maybe it should be
broken up maybe it should be moved
probably doesn't belong in a package
name domain there's also this rule class
here with a cognitive complexity of 37
okay that's not outrageous but again
it's suspicious in a domain package and
so when I look inside I've got these
nested enums group and a little bit of
an arrow formation there and I've got a
whole bunch of member so you'd expect
that in a domain class but then
got some logic so maybe this needs to be
refactored somehow maybe some of this
logic needs to be extracted some we're
going back up to the package level then
again on this I've got this package at
the top called the services package okay
it would be reasonable to expect some
logics in package called services let's
see what's going on there
but maybe this class here with 127 maybe
it's time to break that up let's see
what we got inside again there are zero
issues so there's no single method with
a too high complexity but let's see
we've got a lot of methods in here so
maybe it's time to divide this just to
make future maintenance a little easier
anyway it bears looking at all right so
that's what I wanted to show you guys
about the metric now we have a number
that tells us right off you know that
doesn't correlate to lines of code and
tells us where the hotspots of logic are
in the application alright so now I want
to look at some actual code I said
before that I had zero issues in my
class and so that told me that there was
no single method that had too much
complexity I want to look at some actual
cognitive complexity issues it's this is
the rule that's available in the
mainstream languages should be available
in all of the languages by the end of
the year we've set a default threshold
of 15 in this rule we started at the
threshold of 10 which is the recommended
threshold for cyclomatic complexity and
our internal testing told us that that
was just too strict
so we bumped that up to 15 for most
languages the C family development team
bumped that up to 25 for the C family
languages so C C++ objective-c and so
we're going to be looking at some
methods that are above the allowed
threshold we're going to be looking at
it on a couple of different center cube
servers I'm starting out here on peach
which is an internal instance where we
test new versions of our analyzed
so you guys won't be able to get to this
one these come oh wow I never noticed
that okay apologize to those of you who
are sensitive to that sort of language
[Laughter]
okay so this first method that I wanted
to look at has a cognitive complexity of
24 versus the 15 allowed and first when
I look at one of these methods I want to
just see where the complexity is coming
from
now over here on the right and I know
this is kind of small but I'm afraid
that the comments on the right will go
off oops yeah yeah all right so I can't
make the font bigger but I've got
secondary locations here on the right
which annotate where the complexity
comes in so let's just step through this
make this a little bit more real for you
here on this line I've got a for each
that's plus 1 for the for the loop here
I've got a nested-if so that's plus 2 1
for the if one for the nesting then
another if that's one for the if 2 for
the nesting another if that's one for
the F 3 for the nesting a loop one for
the loop 4 for the nesting here we've
got one for the S 5 for the nesting and
then we come back in down here we're
almost back at the top level so one for
the if one for the nesting and then on
the elf that's just plus one because
again there's no nesting increment on an
Elsa for else we paid that penalty when
we dealt with the if and so that
altogether gives us a total of 24 now
the classic answer to you know how do I
reduce the complexity of a single method
would be to extract some of it into
another method right just spread the
mess around but when I look at this
particular method I noticed something
about it I noticed that inside this
first if is nothing except another if
and inside the second if is nothing but
a third if so I could combine these
three if into one if and that's going to
reduce the nesting level of the
stuff at the lowest level by two it's
going to introduce a sequence of logical
operators that's plus one but on the
whole that's going to drop enough
complexity out of this method to get
it's well below the threshold now not
incidentally that makes this method
easier to read but also notice that
we've dropped the cognitive complexity
of the class as a whole so we've dropped
complexity out of the whole class we've
made the whole application easier to
understand by doing this I was
discussing on the bus last night this
talk with another speaker and he
reminded me of Fred Brooks no silver
bullet and his postulation that there
are two kinds of complexity in an
application
there's the complexity that's required
just to get the job done and then
there's the incidental complexity that's
added by not knowing the best way to do
things
etc and I think what we're looking at is
an example of this incidental complexity
right so with cognitive complexity
pointing out this nesting pointing out
that hey this is really not as easy to
read as it ought to be it helps me find
the places where I need to do some
refactoring so I've got a couple more
code samples I want to look at this one
we're on sonarqube comm this is a public
open instance of sonarqube
any open source project can analyze
their projects for free and hundreds of
them are doing that right now so you
guys can get to this one here we've got
one which is at 34 versus the 15 allowed
and when I look at where the complexity
comes from in this method I've got an if
a nested switch it's not so bad I've got
a top level if a top level if and then
I've got this pattern of top level if
and then a whole bunch of nested Turner
ease all right so I've got all of these
plus plus 2's because I've got nested
ternary operators here oops there
there's my nested ternary and I got a
whole bunch of those I started looking
at this method and I realized that every
one of these nested Turner ease is used
in the same pattern what I'm going to do
is interrogate a JSON object to see if
it has a certain property if it has a
certain
I'm going to extract that value and if
it doesn't I'm going to set a default we
do that over and over and over again
that's + 2 + 2 + 2 - Ching - gene - gene
right so this is crying out to me for
secondary methods a helper method so if
I created a helper method here and
actually we would need 3 we need 1
forget int get string and get double
then we can move almost all of the
complexity in this method off into 3
helper methods those 3 helper methods
are going to have a total of 3 cognitive
complexity because each of them is going
to have an F in it but we've extracted
all of that conditional logic out of
this method and again drops the
cognitive complexity of the class as a
whole made it easier to read easier to
maintain okay this one is also a case
for a helper method we're at 30 vs 215
allowed and we spend a lot of time in
this method testing for string not null
string not empty we do that a couple
times if we extract that into a helper
method we're really only going to save a
few points for the sequences of logical
operators if we really want to get this
method down below the threshold we kind
of have to extract some of this into a
secondary method that decreases the
nesting level of that code that we've
extracted so we get rid of some that
incidental complexity that Brooks was
talking about but I want to point out
here that we're in the landmark shops
project and if I look at another method
in a landmark shops project we also
spend some time in this method doing the
same pattern of string not null string
not empty string not null string not
empty right so if we had extracted that
helper method in the other class then we
could use it for in this class as well
and probably it's common that you have
these patterns that show up over and
over again in applications figure out
how to look them in one place and you've
looked them all over that didn't sound
right but in general when I look at
where the complexity in this method
comes from I see a whole bunch of plus
ones here so we're not doing a lot of
nesting
I think we're looking at the complexity
required to get the job done here so if
you want to get this one below the
threshold you're going to have to bust
out a secondary method just to move some
of that complexity final one I wanted to
show you was this one this method is at
17 versus the 15 allowed now you know
this is the threshold of sex if you're
going to say that a method with
cognitive complexity of 14 is okay you
know what's so much worse than about 16
or 17 right so you know it Eddi
threshold is arbitrary maybe you
wouldn't want to refactor this one maybe
it's not worth the time but what I
noticed when I looked at this method and
you know it's not terrible we've got a
whole bunch of top-level stuff very
little nesting in here but what I notice
is that we've got this sequence of five
caches in a row and if you look at the
bodies of the caches each one of them
does exactly the same thing now in Java
since Java 7 we've had the ability to
catch multiple exception types at one
time
PHP 7 introduces that the newest version
of c-sharp introduces something very
like that as well so if we were to
combine all of these caches into one
then we're going to get rid of four
points for caches here getting us well
below the threshold and not incidentally
making the method easier to read easier
to understand okay so to recap cognitive
Recap
complexity is about understandability if
you need to understand how many the
minimum number of test cases you need to
thoroughly unit test your code base then
there's still a place for cyclomatic
complexity the cyclomatic complexity you
know generally correlates to lines of
code a whole bunch of people found out
in academic studies cognitive complexity
is going to help you understand how hard
the code is to understand how hard it is
to deal with it increments for breaks in
the linear flow it increments for
nesting it ignores readable shorthand
structures again to incent good behavior
when you have a high level of cognitive
complexity it may not need indicate a
need for refactoring but at least it
indicates a need for taking another look
at this and that's it and I think I've
got a few minutes for questions if there
are any and if there aren't I'm doing
office hours tomorrow morning so I the
additional penalty for another little
bit there latter stated target slide for
you to write so let's go back to some of
these code samples that's where I wanted
to be all right so look at this if if
this were at the top level of the method
it would be really easy to understand
but to truly understand what's going on
with us if you have to understand what's
going on here and you have to understand
the choices that were made here and you
have to understand the choices that were
made here and I see you nodding so I'll
shut up at this point yes okay so it's
available today as a rule in Java the
next version of sonar Java which should
go GA this week includes the metric that
we were looking at it's being
implemented I think like as we speak as
a metric in JavaScript it's at I said
it's available as a rule in the
mainstream languages and we hope to have
it available throughout the portfolio by
the end of the year yes sir language we
have over
we will have support for it what I'm
struggling to remember is whether we've
done that yet and I would have to look
at some release notes to tell you
whether it's available today
but it will be available this year we
say it should be available this year
yeah you had a lady time to when you
increment the number is that computable
for a given application No
so there are there is a little bit of
wiggle room but it's not per application
it's per language for instance in COBOL
there's no Elsa structure right and so
but but that doesn't prevent COBOL
programmers from needing to do that sort
of thing right so what you'll see in a
COBOL program is if blah blah blah else
and then nested inside that is another
if now if we followed the canonical
rules just any normal COBOL program
would see an explosion of cognitive
complexity because they don't have the
structure to do it the way modern
programmers would do it right so we give
an exception in COBOL for that similarly
there's an exception in JavaScript for
functions that are used to substitute
for the class structure Eknath script 6
added the class structure but it's not
widely adopted and a lot of really
popular frameworks still sort of require
you to do this sort of so class inside a
function and so we look at the usage of
nested functions in a function to
determine whether this is purely
declarative or whether there's you know
since real logic going on at the top
level so there's a discount
sometimes in JavaScript but it's not
configurable on an application level now
yes sir
do you give any special consideration to
generics engineering structures and
that's a great question and the answer
is no cognitive complexity is about
control flow gave some serious thought
to that sort of thing things that people
consider hard in any given programming
language and the conclusion I came to
was that that's really about the
features of the language for instance
pointer interaction if you're a C
programmer you're used to dealing with
pointer indirection at one level two
level three levels when does this get
hard when should I start incrementing so
basically we ignore language features
and just focus on control flow all right
thank you very much for your time
[Applause]
you
