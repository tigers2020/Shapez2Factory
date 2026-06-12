Introduction
0:07
[music]
The Thesis of AI Engineering
0:14
Yeah, we good. Okay, folks, we're at capacity. Let's
0:20
kick off. I don't want you waiting here for 25 more minutes before we some arbitrary deadline. So, welcome. My name
0:28
is Matt. Uh I'm a teacher and I suppose now I teach AI. Um
0:35
we have a link up here if you've not already been to this which is has the exercises for the um stuff we're going
0:41
to do today. This is going to be around two hours. So we might just sort of kick off two hours from now. Is that right
0:46
Mike? Yeah. Perfect. Um, and the theory behind
0:52
this talk or at least the thesis under which I've been operating for the last kind of six months or so is that
0:59
we all think that AI is a new paradigm, right? AI is obviously changing a lot of things. You guys are obviously
1:04
interested in this and that's why you've come to this talk. And I feel that
1:12
when we talk about AI being a new paradigm, we forget that actually software engineering fundamentals, the
1:19
stuff that's really crucial to working with humans, also works super well with
1:24
AI. And this is what my keynote is on tomorrow. Really, I'm going to sort of be fleshing that out a lot more. And in
1:30
this workshop, I'm hopefully going to be able to direct your attention to those things and uh hopefully show you that
1:38
I'm right, but we'll see. Um, can I get a quick heads up first? How many of you
1:44
guys um are coding have ever coded with AI? Raise your hand if you've ever coded with AI. Perfect. Okay. Uh, keep your
1:51
hand raised. Uh, let's all uh share those armpits with the world. Um,
1:58
how many of you code every day with AI? Cool. Okay. Uh, ra keep your hand raised
2:04
if you've ever been frustrated with AI. Okay. Very good. You can put your hands
2:10
down. Thank you for that show of obedience. I really appreciate that. Um, we are also being live streamed to the Gilgood room as well. I've not uh did we
2:18
send someone up to the Gilgood room to just check they're okay? Don't know. But I see you. Uh, and there is a way that
2:25
you can participate which is we have the um a Q&A. We're going to be doing kind I have a sort of hatred of Q&As's because
2:31
they're not very democratic. The mostly the sort of um most talkative people get to um get to participate and share. And
2:39
so we're going to be going through this um QA here. So why do we have to wait till 3:45? The room is packed. The doors
2:45
are closed. 100% agree. And so if you want to uh ask a question, we're going
2:50
to be I would like you to pile into this async and then we can vote on each other's questions and hopefully get the
2:55
best question surface so the for the entire room to enjoy. So I want to talk about first the kind
3:02
of weird constraints that LLMs have and those weird constraints are sort of what
3:09
we have to base a lot of our work around. Now,
3:14
there's a guy called Dex Hy who runs a company called Human Layer, and he came up with this idea, which is that
3:21
when you're working with LLMs, they have a smart zone and a dumb zone. When
3:28
you're first kind of like working with an LM and it's like you just started a new conversation, you start from
3:34
nothing. That's when the LLM is going to do its best work because in that situation, the attention relationships
3:39
are the least strained. Every time you add a token to an LLM, it's kind of like you're adding a team to a football
3:45
league. You think of the number of matches that get added every time you add a team to a football league. It just
3:51
go scales quadratically. And that's because you have attention relationships going from essentially each token to the
3:58
other that are positional and the sort of meaning of the individual token. And so this means that by around sort of 40%
4:05
or around I would say around 100k is kind of my new marker for this because it doesn't matter whether you're using 1
4:11
million uh context window or 200k. It's always going to be about this.
4:17
It starts to just get dumber. So as you continually keep adding stuff to the
Phase 1: Research & Prototyping
4:23
same context window, it just gets dumber and dumber until it's making kind of stupid decisions. Raise your hand if
4:28
that feels familiar to you. Yeah. Cool. So this means that we kind of want to
4:34
size our tasks in a way that sticks within the smart zone, right? We don't
4:39
want the AI to bite off more than it can chew. And this goes back to old advice like Martin Fowler in refactoring uh
4:46
like uh the pragmatic programmer talks about this. Don't bite off more than you can chew. Keep your tasks small so that
4:53
you as a developer, a human developer don't freak out and don't start acting and going into the dumb zone.
5:01
But how do you tackle big tasks? How do you take a large task like I don't know
5:07
cloning a company or something or just doing something crazy? And how do you break it into small tasks so they all
5:13
fit into the dumb zone? One way of course you could do is I mean kind of what the AI companies maybe want you to
5:20
do or the natural way of doing it is just keep going and going and going. You end up in the dumb zone charging you tons of tokens per request. You then
5:26
compact back down. We'll talk about compacting properly in a minute. And you keep going, keep going, keep going,
5:32
compact back down, keep going, keep going, keep going. And I think that's doesn't really work very well because
5:38
the more sediment, we'll talk about that in a minute. So the theory here is then, and this is what I was doing for a
5:44
while, is I would use these kind of multi-phase plans where I would say,
5:50
okay, we have this sort of number four thing here, this large large task. Let's
5:55
break it down into small sections so that we can then kind of chunk it up and do each little bit of work in the smart
6:01
zone. Raise your hand if you've ever used a multi-phase plan before. Yeah, really common practice, right? This is
6:08
kind of how we've been doing it. Certainly, this is how I was doing it up until December last year really.
6:14
And any developer worth their salt will look at this and go, "This is a loop,
6:19
right? This is a loop. We've just got phase one, phase two, phase three, phase four. Why don't we just have phase n,
6:27
right? Phase n where we essentially just say, okay, we have, let's say, a plan
6:33
operating in the background and then we just loop over the top of it and we go through until it's complete. And this is
6:39
where um raise your hand if you've heard of Ralph Wiggum as a software practice. Okay, cool. Raise your hand if you've
6:45
not heard of Ralph Wigum as a software practice. Actually, that's more like it. Okay. So there's this idea called Ralph Wigum uh which is kind of um sort of
6:52
based on this which is essentially all you need to do is sort of specify
6:58
the end of the journey where you just say okay we create a PRD a product requirements document to say okay let's
7:05
describe where we're going and then we just say to the AI just make a small change make a small change that gets us
7:11
closer and closer to there and Ralph works okay but I prefer a little bit more structure so that's kind where we
7:18
got to in terms of thinking about the smart zone. And that's kind of where I want you to first start thinking about
7:25
here. Another weird constraint of LLM is LLM are kind of like the guy from Momento, right? They just continually
7:32
forget. They could just keep resetting back to the base state. Let me pull up this diagram.
7:38
I sort of I I I really should use slides, but I just prefer just like randomly scrolling around a infinite uh
7:45
TL draw canvas. Thank you, Steve. Um, so let's say another concept I want you
7:52
to have is that every session with an LLM kind of goes through the same stages. You have first of all the system
7:57
prompt here. This gray box here is essentially the stuff that's always in your context. You want this to be as
8:04
small as possible because if you have a ton of stuff in here, if you have 250k tokens, like I have seen people put in
8:11
there, then that you're just going to go straight into the dumb zone without even being able to do anything. So you want
8:17
this to be tiny. [snorts] You then go into a kind of exploratory phase. This blue is sort of where the coding agent
8:24
is going out and exploring the codebase. Then you go into implementation and then
8:29
you go into testing and kind of making sure that it works, running your feedback loops and things like this.
8:34
Raise your hand if that feels familiar based on what you've done. Yep. Sort of the like the the main cornerstones of
8:40
any session. And when you clear the context, you go right back to the system prompt. Bof, you go right back there. So
8:48
you delete everything that's come before. And raise your hand if you've heard of
8:54
compacting as well. Yeah. Okay. There are some people who've not heard of compacting. So let's just quickly show
8:59
what that means. For instance, I've just been having a little chat with my LLM.
9:06
Uh, I want to make sure we sort of, you know, just cover the basics so we're all sort of on the same wavelength here.
9:12
I've just been having a chat with my LLM. I've been talking about a thing that I want to build. How's the font size? Should I bump it up? Folks in the
9:19
back. Bump bump bump bump bump. I'm using claw code for this session,
9:25
but you don't need to use claw code. Uh, in fact, it's often nice not to use claw code. Um, so I've been having a chat
9:33
with the LM just sort of planning out what I'm going to do next. It's asking me a bunch of questions and I can I
9:38
highly recommend you do this. There's this tiny little status line here that tells me how many tokens I'm using. The
9:45
exact number of tokens I'm using. Um I have a article on my website AI Hero if
9:50
you want to copy this. This is oh wow that is that shakes doesn't it? Um, this
9:57
is essential information on every coding session because you need to know exactly how many tokens you're using so that you
10:02
know how close you are to the dump zone. Absolutely essential. And so let's watch it. So I've got two options. I can
10:09
either clear and go back to nothing or I can compact.
10:15
And when I compact then it's going to squeeze all of that conversation which admittedly isn't very much into a much
10:22
smaller space. And this in diagram terms kind of looks like this where you take
10:27
all of the information from the session and you essentially create a history out of it, a written record of what
10:33
happened. And devs love compacting for some reason, but I hate it. I much prefer my
10:42
AI to behave like the guy from Momento because this state is always the same.
10:48
Always the same. Every time you do it, you clear and you go back to the beginning. And so if you're able to do that and you're able to optimize for
10:53
that, then you're in a great spot. So that's kind of the two things I want you to think about with LLM, the two
10:59
constraints that we're working with. They have a smart zone and a dumb zone. And they're like the guy from Momento.
11:06
So let's take a look at the first exercise. And I'm while I'm doing this, the way I want this to work is I'm going
11:12
to sort of show you how um I'm going to be sort of walking through it up here. And I want you folks to be kind of like
11:19
tapping away and doing things as well. So that was just a little lecture bit. Let's now actually get and do some
11:24
coding. For anyone who arrived late or anyone in the Gilgood room, uh go to this link,
11:32
this link up here to see the exercises and clone the repo.
11:38
You absolutely do not have to. You can just watch me do it if you fancy it. But let's go there myself and let's see what exercises await us.
11:45
So essentially, I've built a um this is from my course. This is a uh a course
11:52
management platform essentially a kind of CMS for instructors for students and this is what we're going to be building
11:57
a feature in. So I'm going to take you from essentially the idea for the feature all the way up to building a PRD
12:04
for the feature all the way up to implementing the feature and hopefully you can take inspiration from this
12:10
process and use it in your own work. So
12:15
uh let's kick off. episode. We're going to start by using a skill which is very close to my heart. It's
12:21
the grill me skill. And this grill me skill is wonderfully small, wonderfully
12:28
tiny. And it helps prevent one of I think the main issues when you're working with an AI, which is
12:34
misalignment. The uh the sort of silent idea that I'm
12:41
talking against here, that I'm arguing against is the specs to code movement. Has anyone heard of the specs to code
Phase 2: The Grill Session
12:46
movement? Raise your hand. It's not really a movement. I suppose it's just sort of people saying specs to code. Um,
12:53
what it is is people say, okay, you can write a program or you want to build an app. The best way to build that app is
13:00
to take some specifications. So to write some sort of like document
13:05
and then turn that document into code. So just turn it into code. How do you do
13:10
that? You pass it to AI. if there's something wrong with the resulting code. You don't look at the code, you look
13:16
back at the specs, you change the specs and you sort of just keep going like this. This is kind of like vibe coding
13:22
by another name where you're essentially ignoring the code. You don't need to worry about the code. You just sort of
13:27
keep editing the specs and eventually you just keep going. And I tried this. I really tried it and it sucks. It doesn't
13:33
work because you need to keep a handle on the code. You need to understand what's in it. You need to shape it
13:39
because the code is your battleground. And so this again is where we're going. Let's
13:45
let's get some exercises. So what I'd like you to do is go to this page, the the grill me skill. And inside the repo
13:53
here, we have a Slack message from our pal. Where is it? It's in the
14:00
root of the repo. And it's under
14:05
where is it? Clientbrief.mmd. It's a Slack message from Sarah Chin.
14:11
For some reason, the Claude always chooses Sarah Chen as the name. I don't know why. Um, it's saying that in
14:16
Cadence, our um course platform, our retention numbers are not great.
14:21
Students sign up, do a few lessons, then they drop off. I'd love to add some gamification to the platform. And so,
14:27
when you're presented with an idea like this, you need to find some way of turning it into reality. Let's say Sarah Chen is your client. You're on a tight
14:34
budget. You need to get this done fast. How do you go and do it? Um, raise your
14:39
hand if you would. um enter plan mode when you're doing this. Anyone a big user of plan mode? Yep. Um let's
14:46
actually shout out quickly any other ideas about what you would do with this or raise your hand if you what would be
14:52
your first port of call. Yeah, sorry.
15:00
Yes, exactly. Let's imagine that Sarah Chen's gone on hold. You have no idea, right? Uh she's just posted this thing. You need to action it before you go.
15:07
Well, my first protocol is I go for this particular skill. I'm going to clear my context.
15:15
I'm going to uh get rid of you. You don't need to be there. And I'm going to
15:21
say um I'm going to invoke a skill, which is the grill me skill. Let's quickly check.
15:28
Raise your hands if you don't know what this is. Cool. Oh, sorry. Sorry. Let me be more
15:34
specific. Raise your hands if you don't know what I'm doing here when I uh do a
15:39
forward slash and then type something. Anyone everyone kind of understand what that is? I'm invoking a skill. I'm
15:45
invoking the grill me skill. And what I'm going to do is I'm going to say grill me and I'm going to pass in the
15:51
client brief. So now the LLM really has only a couple
15:58
of things here. It just has the skill and it has the description of what I want to do.
16:04
And this is virtually how I start every piece of work with AI. And while it's
16:09
exploring the codebase, I'm just going to show you what the grill me skill does. So this is inside
16:15
the repo so you can check it out. It's extremely short. Interview me
16:20
relentlessly about every aspect of this plan until we reach a shared understanding. Walk down each branch of the design tree, resolving dependencies
16:27
one by one. For each question, provide your recommended answer. Ask the questions one at a time. uh blah blah
16:33
blah. What this does, and what I noticed when I was working with AI, especially in plan mode actually, is it would
16:42
really eagerly try to produce a plan for me. It would say, "Okay, I think I've got enough. I'm just goof plan."
16:49
And what I found was that I was really trying to find the words
16:55
for this for for what I wanted instead of that. And Frederick P. Brooks in the
17:00
design of design he has a great quote uh talking about the design concept when
17:06
you're working on something new with someone when you're uh all trying to build something together
17:12
then there's this shared idea that's shared between all participants and that is the design concept and that's what I
17:18
realized I needed with Claude I needed I needed to reach a shared understanding
17:25
I didn't need an asset I didn't need a plan I needed to be on the same wavelength as the AI as my agent. And
17:31
this is an extremely effective way of doing it. So hopefully there we go. Nice. It has done its exploration. First
17:38
of all, it's invoked a sub agent which spent uh 97 93.7K tokens on Opus.
17:47
Um and it's asked me the first question. Cool. We can see that even though the
17:52
sub agent burned a ton of tokens, I haven't actually um uh increased my
17:58
token usage that much. Raise your hand if you don't know what sub aents are. It's an important question. Everyone
18:05
kind of clear what sub aents are? Okay, I'll give a brief definition which is that this this sub aents thing here,
18:10
this explore sub agents, it has essentially gone and called another LLM which has an isolated context window
18:18
and then that LLM has reported a summary back. So a sub aent is kind of like a delegation. You're delegating a task to
18:24
a sub agent. It goes eagerly does all the thing, explores a ton of stuff and then just drip feeds the important stuff
18:30
back up to the orchestrator agent to the parent agent. So, okay. So, hopefully
18:36
you guys have seen the same thing. It's done on explore. And we now have our first question. Points economy. What
18:42
actions earn points and how much? Okay. At this point, you can ask it, by the way, questions to um deepen your
18:49
understanding of the repo. I obviously know this repo really well because I wrote it, but you might not um know what's going on. So, let's say my
18:57
recommendation, keep it simple, twopoint sources to start. What's so nice about this is that not only does it give us a
19:03
question that kind of aligns us here, we get a recommendation, too. And often what I'll find is the AI's
19:09
recommendations are really good. And so I'll just say skip video, watch events, they're noisy and gameable. I agree.
19:16
Sarah's asked while keep lessons in the bread and butter. Yeah,
19:21
looks good, pal. [snorts] Now, what I usually do is I usually dictate to the AI. I'm usually
19:28
actually chatting to the AI instead of uh typing here, but uh this is a relatively new laptop and I couldn't get
19:34
my dictation software working on it um because Windows is crap. Um
19:41
so should points be retroactive? There are existing lessons progress records. We're completing out timestamps. This is
19:47
a really nasty question, right? Should we actually go back and backfill all of the lesson progress events? This is a
19:53
kind of question that you need to be aligned on if you're going to fulfill the feature properly. This is not something I considered and Sarah Chen
19:59
certainly didn't consider. Do I want it to be retroactive? H. Let's actually do
20:05
a vote inside here. Should we go back and backfill all the records? Raise your hand if you think we should backfill all
20:10
the records. Raise your hand if you think we shouldn't backfill all the records.
20:17
There are a lot of uh fence sitters in the room. I'm going to say, you know, this is the kind of discussion
20:23
you're sort of having with the AI. You're getting further aligned. Yes, I'm just going to go with this recommendation because I'm lazy.
20:31
Notice, too, how I'm able to keep in the loop here with AI. I'm not, you know, it's it's pinging me these questions
20:36
pretty quickly. I'm not having to go off and check Twitter or something. Levels. What's the
20:43
progression curve? Yeah, that looks about right, for instance. Yes. Okay. So hopefully you should be able to go and
20:49
um kind of work through this with the AI [clears throat] and essentially try to
20:55
reach an alignment. And this grill me skill this can last a long time. This can I've had it ask me 40 questions.
21:01
I've had it ask me 80 questions. I've had some people it asks a hundred questions to literally you're sat there
21:07
for an hour chatting to the AI. And what you end up with is essentially this conversation history that works really
21:14
nicely and works really nicely as an asset of the design concept that you're creating. This can also function like
21:21
this. You can uh have a meeting with someone who's a maybe a domain expert. Maybe I have a meeting with Sarah. I
21:27
feed that meeting transcript into uh I don't know Gemini meetings or whatever
21:32
you guys are using. You take that, you feed it into a grilling session and you grill through the assumptions that you
21:38
didn't have. So, this ends up being a really nice kind of um a really nice way
21:43
of just taking inputs from the world and then just turning and validating them.
21:49
So, okay, let's see. I really want to get to the end of this, but I also don't want to
21:54
just like be sat here talking to the AI in front of you for uh a thousand days. So, I'm just going to say yes.
22:03
Let's see what happens. So, I tell you what. Um, while you guys sort of have a little fiddle with this locally, let's
22:09
start a little Q&A session now. And let's see how's this going to work. Can
Phase 3: Writing the PRD
22:15
we keep the door closed? I'll turn up the microphone. It's quite noisy. Uh, let's see. Mike, can we uh Door closed?
22:23
Oh, it has been closed. Mark has answered. Beautiful. So, what I'd like you to do is there any air con? Yeah,
22:30
there is some air con. I think there is some air con you guys aren't being lit
22:35
here. I'm being I'm being fried alive here. Uh so what I'd like you to do is go on to the slideo which you can join
22:42
here. Have a if if you're not taking the exercise, go on to the slideo, have a little fiddle and vote on some good
22:48
questions. I'm just going to chat to the AI for a second uh until we reach a stopping point. So do streaks earn
22:54
points? Um, streaks are standalone.
23:06
Let's see what else it comes up with.
23:12
Where does gamification UI live? Let's have it in the dashboard.
23:19
I'm just going to scan these and blast through them basically. So, how we doing with our slido?
23:24
Okay. Have I tried specit open spec or taskmaster instead of the grill me
23:30
skill? Do I find them more verbose or a structured alternative? This is a great question. So there are a ton of
23:35
different frameworks out there that allow you to um sort of build up this planning process for you. I personally
23:42
believe you at at this stage when there's no clear winner, when there's no kind of like one true way and when
23:48
things are changing all the time, you need to own as much of your planning stack as you possibly can. What I've
23:55
noticed and a lot of my students is they tend to overuse a certain stack.
24:03
they get into trouble and they because they don't own the stack and they don't have observability over the whole thing,
24:09
they just go, "This isn't working. This sucks." Whereas if um if you have
24:15
control over the whole thing, then at least you know how to fix it or potentially know how to fix it. So I'm
24:22
even though I'm sort of giving you uh a stack basically, I believe in inversion
24:28
of control and you should be in control of the stack. So, can I press zero, please?
24:38
Sorry. Sorry, that was a lot of sort of mumbling. Can I feedback? You have four options on the
24:44
bottom of you to hit dismiss. Thank you.
24:50
I'm so sorry. [laughter] Well, you didn't want to give Claude good feedback. Why? What's wrong with you?
24:58
Okay, cool. Uh many of the questions asked by the grill me skill are not necessarily appropriate for a developer rather a PO
25:04
in larger teams who should use it. Yeah. Um raise your hand if um you've ever
25:10
done pair programming. Anyone ever done pair programming? Right. Keep put your hands down and raise your hand again if
25:16
you've ever done a pair programming session with an AI. Right. How did it go? Was it good? You
25:23
enjoy it? I think pair programming sessions with AI is a great idea because you've got a third person in the room
25:28
who will relentlessly quiz you and ask you questions. It should if you don't know the answer, it should be you, the
25:33
domain expert and the AI in the same room. If you have a question about implementation, it should be you, a
25:39
fellow developer and the AI in the same room. You know, you can be sort of working through these questions in your team. And I think actually we're going
25:47
to look at implementation in a bit and we're going to see how you can make implementation so much faster. And but I
25:54
think the really crucial decisions, the ones you need humans for, you actually need a lot of humans and it doesn't
25:59
really matter how many humans are in there. You can actually throw a bunch like a kind of like mob programming with
26:04
AI essentially. Uh what's my favorite metaprompting tool? I think I kind of answered that.
26:10
Uh there's no air con. Let's just live with it. Uh, how do I use the conversation as an asset after the grill
26:16
me session? Well, we're going to get there. Um, okay. So, I really want to
26:24
I want to speed this up sort of artificially. Just what
26:30
I This is the thing. So, someone just said, "Okay, Ralph loop this." But this is crucial because I can't loop over
26:36
this, right? I can't um I think of there as being two types of tasks in the AI
26:42
age where you have human in the loop tasks where a human needs to sit there
26:47
and do it which is this we are the human in the loop with multiple humans in the loop and there are AFK tasks there are
26:55
tasks where the human can be away from the keyboard and it doesn't matter implementation as we'll see can be
27:00
turned into an AFK task but planning this alignment phase has to be human in
27:06
the loop has to be. So, I've got to do it, unfortunately.
27:11
Um, I don't know. Uh, give me a long list of all your recommendations.
27:20
I'm running a workshop right now, so I artificially
27:26
need you to pull more weight.
27:31
So, let's see what it does. Uh, let's answer a couple more questions while it's doing its thing.
27:37
What is my opinion on PMS or other non-dev rolls vibe coding task?
27:45
Um, I'm going to return to this later. I think I'm going to leave this unanswered.
27:51
A bit of mystery. I notice I'm not using the ask user questions UI for grill me. Why? Um,
27:57
there's a specific uh UI that you can bring up in claude code which I'll answer this just quickly. uh ask me a
28:05
question using the ask user question tool. [snorts] And this UI um is just
28:12
sort of broken in Claude and I really hate it. You notice I'm using Claude, but I don't
28:19
like Claude very much. Like you you really are free with this method to choose any um system you like. And this
28:24
is what the UI looks like. It's very pleasing when you first encounter it, but then you realize it is actually broken in a ton of different ways.
28:32
All right, what did it come back with? Oh, blime me. Oh, no.
28:38
So, while this is doing its thing, let me do some teaching in the meantime. The plan
28:44
here is that we take our grill me skill and we need to essentially find some way
28:49
of turning it into a destination. We need to go down to the uh we
28:57
essentially need to we're figuring out the shape of this. That's what we're doing. figuring out the shape of the
29:03
tasks during the grilling session. And in order to turn it into a bunch of
29:09
actionable actions for the AI, we essentially need to figure out the destination. We need to know where we're
29:15
going. We need to know the shape of this entire thing. So I think of there as being two essential documents that we
29:21
need. We need a document that documents the destination.
29:27
Oh no, it's so not bright enough. There we go.
29:33
Still not bright enough. There we go. We need something to document the destination and we need something to
29:39
document the journey. In other words, we need something a document that's going to figure out what this even looks like
29:46
in all of its user stories and figure out a definition of done. And then we need to figure out what the split looks
29:52
like. So that's where we're going to go to next. So once we finish with the grilling session.
29:59
Yeah, it looks great. Fantastic. I love it. It answered it answered 22 of its
30:04
own questions. There you go. That's quite representative of what a grilling session looks like.
30:09
So at this point now I have used 25k tokens and all of that or loads of that
30:17
stuff is gold. I want to keep that around. I've I've got 25k great tokens
30:23
there. And what I want to do is kind of summarize it in some kind of destination document. So this is um the next
30:30
exercise where we're going to uh we're going to write a product
30:37
requirements document. And the product requirements document or the PRD is
30:43
essentially that's its function. It's the destination document. And it sort of doesn't matter what shape it is. I've
30:51
got a shape that I prefer and that I quite like, but you can just choose your own shape or whatever your company uses.
31:00
And all we're really doing is too worried about that.
31:05
All we're really doing is summarizing the design concept that we have so far. And
31:12
the So let let's try this. So I'm going to initiate this. I'm going to say zoom
31:17
all the way to the bottom. All I'm going to do is just say write a PRD.
31:23
And we can take a look at that skill now. Write a PRD.
31:29
So this skill, it does a few things. It first asks the
31:35
user for a long detailed description of the problem. You can use write a PRD without grilling first, but I just like to grill first and then write the PRD
31:41
afterwards. Then you can um get it to explore the repo, which we've kind of already done. Then we get it to
31:49
interview the user relentlessly. So have a kind of grilling session again. And then we start um putting together a PRD
31:56
template. So this is available in the repo if you want to check it out. And essentially this is what it looks like.
32:01
We've got some problem statements, the problem the user is facing, the solution to the problem, and a set of user
32:06
stories. And these user stories sort of define what this is. You know, as you you guys have probably seen things like
32:12
this if you've been a developer at all. um you know there are cucumber is a language you can use to write these in or we just sort of um uh write them
32:20
ourselves essentially. Then we have a list of implementation decisions that were made and a list of crucially
32:26
testing decisions too. So I'm going to run this. Okay. And so it's
32:33
finished its thing. Ah Windows let me close the thing. Thank
32:39
you. I don't know why I bought a Windows laptop. I think I just I like the challenge. Um
32:46
[clears throat] so the first thing that it's going to give me are a set of proposed modules it wants to modify.
32:54
Now there's a deep reason why I'm thinking about this. So this is at this stage we have an idea. We have sort of
33:02
speced out the idea. We've reached a sort of understanding of what we're trying to do. And then we need to start
33:09
thinking about the code because at this point we need to this is not specs to
33:14
code. This is not where we're ignoring the code. We actually keep the code in mind throughout the whole process. And
33:21
the way I like to do this is I like to just sort of think about a set of proposed modules to modify. We're going to return to this this idea of
33:29
continually designing your system and keeping your system in mind. So it's it's saying recommend test for the
33:34
gamification service is the only deep module with meaningful logic. These modules look right. Yeah, that's good.
33:44
And it's going to ping out a PRD. Now for ease of setup, I've got it so
33:51
that it creates a set of issues locally. So it's just going to create essentially a PD inside this issues directory. But
33:59
the way I usually do it, and you can check this out yourself, is you can go
34:04
to my um essentially what I consider my work repo, which is github.com/mattpocco/course
34:12
video manager up here. And in here, this is essentially a app that I create um
34:19
that I use all the time to record my videos and things like this. I think I've recorded like I pulled down the
34:25
sets. I think I've recorded like a thousand videos in here or something nuts. Um, and you can see here that it's got 744 closed issues. And this is
34:33
essentially all of the uh PRDs and all of the implementation issues that I've put into here. So, this is how I usually
34:39
like to do it. [clears throat] So, that's what I'm doing with the There
34:45
we go. Yeah, I'm just going to say yes and uh and get that issue out. Let's see. It is
34:52
inside here. So, we got the problem statement. people sign up for courses,
34:58
uh the solution, the user stories, uh 18 user stories, looks nice, some implementation decisions, level
35:03
thresholds, etc. This is enough information. We've kind of clarified where we're going and what we're doing.
35:09
So that's what we do. We essentially have a grilling session and we've created an asset out of it. Now, raise
35:15
your hand. Should I be reviewing this document? Raise your hand if you think I
35:20
should be reviewing the document. Yeah, I don't I don't look at these. I don't look at these. The reason I don't
35:27
look at these is because what am I testing at this point? What am I like when I read it?
35:33
What am I testing? What am I what are the failure modes I'm trying to test for? I know that LLMs are great at summarization because they are they're
35:40
really good at summarization. I have reached the same wavelength as the LLM, right? Using the grill meme skill, we
35:46
have a shared design concept. So if I have a shared design concept, all I'm doing is I'm just essentially checking
Phase 4: Slicing Work into Issues
35:53
the LLM's ability to summarize. So I don't tend to read these.
36:00
Let's have let's have a Q&A because I can feel you guys are itching for it. And then I think we might have like I
36:06
don't know just a five minute comfort break just to rest my voice and so you can catch up with the exercises for a minute if that's all right. So let's
36:11
have a little Q&A sesh. Uh, if I don't like clawed code, which one do I
36:17
actually like? Um, uh, have you ever heard the phrase, um,
36:23
uh, democracy is the worst way to run a country apart from all the other ways? That's how I feel about claw code.
36:30
Uh, we've answered that one. Uh, what's your thoughts on developers
36:36
needing to very deeply understand Typescript now that fix the TS make no mistakes exist? I don't understand the
36:42
phrasing of this but I think I understand the meaning which is that
36:48
I believe that code is very important and this is kind of going to feed through the whole session and that bad
36:54
code bases make bad agents. If you have a garbage codebase you're going to get garbage out of the agent that's working
37:01
in that codebase. We'll talk more about that in a bit. And so I think understanding these tools very deeply,
37:06
understanding code deeply is going to make you a much much better developer and get more out of AI.
37:14
Uh, and that answers that question too. Sweet. Uh, get out of it. There you are.
37:24
Now that we have 1 million tokens available, do we ever actually want to take advantage of that?
37:30
I've noticed that the dumb zone has become less dumb lately. Okay, great question. This goes back to our kind of
37:35
initial idea on the dumb zone.
37:41
Uh I um I recorded my Claude Code course
37:46
using a 200k context window and on the day that I launched the course, they announced the 1 million context window.
37:53
My take on this is that what Claude code did is they essentially just did this.
37:58
They shipped a lot more dumb zone to you essentially. Now, this is good for tasks
38:03
where you want to retrieve things from a large context window. If you want to pass five copies of War and Peace or
38:09
something to it, and you want to find out all the things that uh uh I can't remember a character from War
38:15
and Peace. Uh why did I start with that? It's good for retrieval. It's less good for coding. So, I consider that it is
38:24
about 100K at the moment is the smart zone. the smart zone will get bigger and
38:30
that will be a really nice improvement. So folks, we're going to take like a five minute comfort break if that's all
38:36
right just for my voice and so maybe you can have a little move around or something or grab a drink. I can just
38:41
notice some sleepy eyes and I want to make sure that we're awake for the next bit if that's all right. So we'll take five minutes and I'll see you back here
38:49
then. All right. So we have our PR which I'm not going to
38:55
read a kind of destination document. Let's quickly scan for any good questions before we zoom ahead.
39:02
And rediscovering the role of software engineer in today's world. Top three
39:08
disciplines you recommend. Um, taekwondo is good. I've heard I' have no idea how
39:13
to answer this question. Um, thank you for asking it though. Um, top three disciplines I recommend.
39:21
I mean, sorry, plumbing. Plumbing is a good one. Yeah. Yeah. Yeah. I don't know if that's a discipline. The plumbers I've hired are
39:27
not usually very disciplined. Um, right.
39:32
So, okay, we now have our destination. Okay. Um, perfect.
39:39
So, how do we actually get to our destination? How do we We have a sort of vague PRD. How do we split it so that we
39:46
don't put things into the dump zone? In other words, we have our number four. How do we split it into this kind of
39:52
multi-phase plan? Well, probably what you would do at this point is you would say, "Okay, Claude, give me a multi-phase plan that gets me to this
39:59
destination." Right? That sort of makes sense. This is what we've been doing before, but I have um a sort of better
40:04
way of doing it now, which is that I like creating a canban board out of
40:12
this. Raise your hand if you don't know what a canban board is.
40:17
Cool. Okay. A camon board is essentially just a set of tickets that you put on the wall that have blocking
40:23
relationships to each other. So, we're going to see what it kind of looks like here. This is how we've worked um as
40:30
developers for a long time, really since agile came around. And what it does, we
40:35
can see it here. It has proposed that we split this setup into um five different
40:42
tasks. Here we have the first one which is the schema and the gamification service. Yeah, that looks pretty good.
40:48
This is blocked by nothing. And we can even see here that it's a it's given it a type of AFK, too. Remember I talked
40:55
about human in the loop and AFK earlier. This is an AFK task. This is something we can just pass off to an agent to do its thing. Streak tracking. Okay, that
41:02
looks good. Uh then wire points and streaks into lessons quiz completion. This is blocked
41:08
by one and two. Retroactive backfill. This is blocked only by one. And then
41:14
this one here is blocked by all of the tasks. Cool.
41:19
H. Now I consider this, you could say, why don't we just make this sort of
41:25
generation of the issues? Why don't we just hand that over to the AI? Why do I need to be involved here? Right? Because
41:30
it's given us quite a good selection of tools here. Why do I need to review this and sort of figure out what's next? Now,
41:37
my take here is that this is really cheap to do, like very quick to do once I've done the PR. And I can immediately
41:44
see some issues here. There's a really, really important
41:49
technique when you're kind of figuring out what the shape of this journey should look like. And
41:57
it sort of comes to this very classic idea uh which comes from pragmatic programmer called tracer bullets or
42:04
vertical slices. and traceable. It's really transformed the way I think about actually
42:11
getting AI to pick its own tasks. Systems have layers, right? There are
42:17
layers in your system. These might be different deployable units. You might have a database that lives somewhere.
42:23
You might have an API that lives maybe close to the database but in a separate bit. You might have a front end that lives somewhere totally different like a
42:29
CDN. Or within these deployable units, you might have different layers within
42:34
those. In for instance the codebase that we're working in, we have a ton of different services servers. We have a
42:41
quiz service, a team service, user service, coupon service, course service. And these services have dependencies on
42:47
each other. So they're kind of like individual layers. Well, what I noticed
42:53
is that AI loves to code horizontally. So it loves to code layer by layer. So
43:00
in other words, in phase one, it will do all of the database stuff, all of the schema, all of the, you know, all the
43:06
stuff related to that unit. Then it will go into phase two and do all of the API stuff. Then it will add the front end on
43:12
top of that. Does can anyone tell me what's wrong with that picture? Why is that not a
43:18
good thing to do? Raise your hand if you have an answer. Yeah. Have the whole feedback loop.
43:23
Exactly. You don't get feedback on your work until you've really started or
43:29
completed phase three. So what you really need to do is you're
43:35
not until you get to phase three, you're not actually testing that all the layers work together.
43:41
You haven't got an integrated system that you can test against. And so instead you need to think about vertical
43:47
layers. You need to think about thin slices of functionality that cross all of the layers that you need to. And this
43:55
is a much better way to work, much better way for the AI to work too because it means at the end of phase one
44:01
or during phase one, it can get feedback on its entire flow. So what this means to me
44:07
is inside the PRD to issues skill up here I have got break a PRD into
44:15
independently grabbable issues using vertical slices traceable it's written as local markdown [snorts] files we
44:21
first locate the PRD uh again explore the codebase if this is a fresh session we draft vertical slices
44:28
so we break the PRD into tracer bullet issues a traceable bullet by the way is
44:33
Uh, essentially when you're like an anti-aircraft gunner, it's quite a violent idea actually, uh, and you're
44:40
looking up in the sky and it's night, if you're just shooting normal bullets, you have no idea what you're firing at, right? You could just be, you know, you
44:46
see the plane, but you don't see where your bullets are going. Tracer bullets is they attach a tiny bit of phosphoresence or phosphor or something
44:53
to make it glow as it goes. So, this means that every sixth bullet or something, you actually see a line in
44:58
the sky. So, you have feedback on where you're aiming. So this is what this is the idea here is that we increase our
45:05
level of feedback and we get near instant feedback on what we're building because without that the AI is kind of
45:11
coding blind until it reaches the later phases. We've got some vertical slice rules. We quiz the user and then we
45:17
create the issue files. So what I see here is that even though I've I've told
45:24
it to do vertical slices, it's proposing to create the gamification service
45:32
first on its own. That's just one slice there. And that to me feels like a horizontal slice. What I want to see in
45:38
the first vertical slice especially is I want to see the schema changes or some schema changes. I want to see some new
45:45
service being created and I want a minimal representation of that on the front end. So I want it to go through
45:50
the vertical slices, not just the horizontal. Does that make sense? Okay. So I'm going to give the AI a
45:57
rollicking. Uh bad boy. No, I'm not going to waste tokens just being
46:04
just memeing. Um so the first slice is too horizontal. I'll just start with
46:10
that and see if it picks it up. Does that make sense as a concept? And I think having that um what I really like
46:17
about going back to those old books is that we are really trying to in this day and age like get
46:25
uh verbalize best software practices in English. And these books, 20-year-old
46:30
books have already done that. And it's an absolute gold mine if you want to throw that into prompts. But even with that, it's not going to um not going to
46:37
do a perfect job each time. So, award points for lesson completion visible on
46:43
dashboard. Yes, that's a beautiful vertical slice because it's definitely a big chunk of stuff. It's doing a lot of
46:49
stories there, but we're going to see something visible at the end and the AI will then just be able to add to that.
46:55
You see why that's preferable to the first one. Cool. Uh, looks great.
47:01
So, we're getting closer now. And anyone following at home as well, you're not at home, but you get the idea. um we'll
47:08
hopefully see the same thing too and start developing the same instincts. Let's open up for questions just while
47:13
I'm sort of creating these GitHub issues or not GitHub issues uh local issues.
47:20
When will I stop using Windows? Never. What is your uh Okay, we'll get to that later.
47:26
How does AI um decide when to stop grilling? Because AI can ask incessantly. Can we have a smarter way
47:31
to decide the stop point? Yeah, it does tend to really um those grilling sessions can be super intense. And the
47:37
thing about these skills is you can tune them if you want to. If you feel like the AI is just absolutely hammering you,
47:42
hammering you, hammering you, then you can just tell it to just pull back a little bit or get it to do, you know,
47:48
stop points and that kind of thing. So, if that's a failure mode that you run into a lot, then you just, you know, change the skill.
47:55
Uh do I still use uh be extremely concise, sacrifice grammar for the sake of concision? Um there was a tip that I
48:01
gave folks um five months ago which is that to basically increase the
48:07
readability of your plans. So when you're using plan mode then you can put it in your claw.md
48:13
and you can say okay yeah approve that. Let's open up claw.md.
Phase 5: Implementation with AI Agents
48:21
Do I have a claw.md? Maybe I don't. I I really don't use clawd very much. I'm just going to put a dummy inside here.
48:28
Um when no when talking to me
48:33
uh sacrifice grammar for the sake of concision
48:40
and this um prompt was uh really useful to me when I was reading the plans because it meant that the plans would
48:46
come out and they would be very concise, really nice, easy to read, often very uh concise. But I've since dropped this
48:54
idea in preference to a grilling session because what I noticed was it just I
48:59
didn't want to read the plans. I wanted to get on the same wavelength as the LLM. I wanted it to ask aggressive questions to me. And when I stopped
49:05
reading the plans, I stopped needing them to be concise. So I think of the plans really in the destination document
49:11
as uh the end state. And I don't need that end state to be concise. Hopefully that answers your question.
49:19
Uh, what do I think will be the outcome of the Mexican standoff of future roles of PMS and other roles converging? Uh, I
49:26
have no idea. I'm not a pundit. I have no idea. Uh, okay. So, we should uh after a
49:34
couple of approvals uh end up with a set of issues. Now,
49:40
these issues that we're creating, they're designed to be independently grabbable, which means that this canon
49:47
board ends up looking kind of like this where you have
49:53
essentially a set of tickets with a whole load of independent relationships. So, this one needs to be done before
49:59
this one. This one needs to be done before this one. And this one, let's say we got another one over here. This one
50:05
needs to be done before this one. This means that you can start to parallelize.
50:11
You can start to get agents working at the same time on these tasks because yeah, this one needs to be done first
50:18
and then these two can be grabbed at the same time by
50:24
independent agents. Raise your hand if you've done any kind of parallelization work with agents. Okay, cool. So this
50:32
allows you um to turn those plans into optimally kind of like into directed
50:38
asyclic graphs essentially where you just are able to um essentially have
50:43
three phases here where you have phase one.
50:49
Let me grab move that uh above this line here you do this one.
50:56
Then phase two you do the two below it. And then phase three you do this third one. and add it onto there. And when you
51:03
think about there could be this could this is a relatively simple plan but you could have many different plans
51:08
operating all at once. It means that you can do really nice parallelization and we'll talk more about that in a bit. But
51:14
that's why I prefer a canon board set up like this to a sequential plan because a
51:20
sequential plan can really only be picked up by one agent. So this where
51:26
did it go? Over here. Yeah, this plan here, this is really
51:32
only one loop, right? Only one agent can work on these because we have numbered phases and they're not parallelizable.
51:38
Does that make sense? Cool. So, we've got our issues. Ah, come on.
51:44
Stop asking me for Oh, no. It's creating them on GitHub. I really don't want that. Oh, no. You fool.
51:53
Create them in issues instead. No, that's not precise enough. Uh, you
52:00
fool. Create them in local markdown files instead referencing the local
52:08
version. Sorry about this.
52:15
So, once we get to this point, we [clears throat] have a bunch of issues locally that we can start um looping
52:23
over and implementing. And it's at this point that the human leaves the loop.
52:28
So, so far, let me pull up a a proper overview of this kind of flow that we're exploring
52:35
here. So far,
52:40
we have taken an idea, zoom this in a bit for the folks at the back,
52:47
and we've grilled ourselves about the idea. We can skip over research and prototype,
52:52
but we've turned that into a PRD into a destination document. We've then turned that PRD into a canon board and all of
53:00
those steps are human reviewed. And now the implementation stage, we step back
53:08
and we let an agent um work through that camp board or multiple agents work through the camp board.
53:15
Now, what this means is that yeah, we've spent a lot of time planning here, but it means that we've queued up a lot of
53:21
work for the agent. We can think of this as kind of like the day shift and the night shift. This is the day shift for
53:26
the human, right? Planning everything, getting all the uh all the stuff ready and then once we kick it over to the
53:32
night shift, the AI can just work AFK. But what does that look like?
53:37
Well, so I'm just going to Oh, yeah. Just allow it. It's perfect. So this looks like if we head to the
53:45
next exercise which is
53:51
uh in fact the last exercise here running your AFK agent. Now
53:57
I've called this uh Ralph really because it is a it is essentially a Ralph loop and this prompt here I want to walk
54:04
through this really closely. The first thing it's doing here is we're essentially going to run Claude and
54:10
we're going to basically try to encourage it to work um completely AFK.
54:16
I'll show you what the sort of script for this looks like in a minute, but you say, okay, local issue files from issues
54:21
are provided at the start of context. The way we do that is if you look inside once.sh SH here inside the repo
54:29
we have uh it's essentially just a bash script where we grab all of the issues
54:37
[clears throat] um which are inside markdown files and we cap them into a local variable. So that issues variable contains all of the
54:43
issues that are in our entire backlog. Then we grab the last five commits. I'll
54:50
explain why in a minute. And then we grab the prompt and we just run claude code with permission mode except edits
54:58
and then just essentially just pass it all of the information. This is what the implement looks like. So that's what a
55:05
very very simple version of this sort of loop looks like. And of course this is not a loop. This is just running it
55:10
once. The loop is in the AFK version up here which is uh a fair bit more complicated.
55:18
And the crucial part here is we're running it in Docker sandbox as well. So I I don't want you to install Docker on
55:25
your laptops because we're just going to be like you need to download a special image and we're going to tank the conference Wi-Fi if we do that. So I I
55:32
am going to demo this to you, but you um won't need to run this yourself. But I'll talk through this in a minute. But
55:37
essentially this once loop here,
55:44
we're just essentially running one version of the thing that we're going to loop again and again and again. So this
55:50
is kind of like the human in the loop version. And this is essential. Running this again and again is essential because you're going to see what the
55:56
agent does and see how it ends up working. And any tuning that you need to add to the prompt, then you can do that.
56:03
Let's go to the prompt. Um,
56:09
so local issue files are being passed in. You're going to work on the AFK issues only. That makes sense. If all
56:16
AFK tasks are complete, output this no more tasks thing. And then the next thing, pick the next task. So
56:26
what we're doing here is we're essentially running a backlog or curating a backlog that our AFK agent is
56:32
going to pick up. That's the purpose of all of these um setups in the beginning
56:38
in this uh all the way to this canon board here. We're just essentially creating a backlog of tasks for the
56:44
night shift to pick up and the night shift this sort of Ralph prompt here.
56:50
It's got its own idea about what a good task looks like. So next pick up I'm I
56:56
did talk about parallelization. I will show you this later, but this is essentially a sequential loop here.
57:01
we're just going to run one coding agent at a time. This is a good way to just sort of um get your feet wet
57:06
essentially. So, it's prioritizing critical bug fixes, development infrastructure, then
57:13
traceable bullets, then polishing quick wins and refactors. And then we just have a very simple kind of instruction
57:19
on how to complete the task. So, we explore the repo, use TDD to complete the task. I'll get to that later.
57:27
And we then run some feedback loops. So let's let's just try this and let's just see what happens. So good. It's created
57:34
the issue files. We should be good to go. I'm going to cancel out of this. I clear and I'm going to run
57:40
uh where is it? Ralph once.sh. And you can feel free if you're following along
57:46
to do the same thing. So we can see it's just running Claude inside here with the prompt and with all
57:53
of the issues that have been passed in. And while it's doing its thing,
57:59
you probably have some questions about this setup and about the decisions that I've made to essentially delegate all of
58:06
my coding to AI, right? So, let's let's do a quick Q&A while it's uh getting its feet under.
58:14
Uh, okay. I'm going to just
58:19
remove those. How do you retain negative decisions?
58:25
things that you decided against and ration when persisting the results from the Grommy session. A great question.
58:31
That's a very simple answer which is the in the PRD uh write a PRD section there
58:37
is a stuff at the bottom a section of the things that are out of scope. So the things we're not going to tackle in this
58:43
PRD which is very important for giving a definition of done. Feel free to ping on the slido if you've
58:49
got any more questions. Uh what's my front end workflow? Okay, that's a great question. I'm gonna I'm
58:55
gonna answer that in a minute, I think. How to deal with agents producing more
59:00
code that we can review? How to properly parallelize and use multiple agents in a separate way? Okay, that's um there's
59:06
two questions there. Um raise your hand if you feel like you're doing more code
59:12
review now than you used to. Yeah, definitely. Um I don't think
59:19
there's a way to avoid this. If we delegate all of our coding to
59:25
agents, you notice that the implementation here is really the only AFK bit. We then also
59:32
need to QA the work and code review the work, right? And if we are running these
59:38
loops where it's essentially going to implement four issues in one, it's hard to pair that with the dictim that you
59:46
should keep pull requests small and self-contained, right? like small self-contained pull requests means
59:52
you're needing to do fewer loops or shorter loops or something. Or maybe you
59:57
do like a big stack of PRs, but that seems horrible as well. That's still just more separated code to review. I
1:00:03
don't honestly know what the answer to this yet. I think we just need to be ready to be doing more code review
1:00:09
essentially, which is not fun. That's not a fun thing to say. That's not like I don't know. I don't feel good saying
1:00:14
that, but I do think it's probably the the way things are going. It's a great question.
1:00:22
Uh, can we grab a couple of questions from the room as well? Let's not we won't do
1:00:27
the mic, but uh raise your hand if you've got a question for me immediately. Yeah. So, the approach looks very linear from
1:00:34
an idea to QA. Of course, the real world is a lot more messy. So you have all these ideas that
1:00:42
are in parallel and full picture and while you're working on something else
1:00:48
comes in. Yeah. How do you deal with the messiness? How do you feedback?
1:00:53
Great question. So the question was if this all looks great if you're a solo developer, but actually how do you
1:00:58
implement this in a team? How do you gather team feedback on this? And my answer to that is that if you have an
1:01:04
idea up there and essentially the sort of journey from the idea to the
1:01:11
destination is something you need to figure out with the team, right? So all of this stuff up here, this is kind of
1:01:17
like team stuff, you know what I mean? So if you have an idea and you do a grilling session on it and you have a
1:01:23
question that you don't know how to answer, then you need to loop in your team as we described before. Then you
1:01:28
might need to go, okay, we just need to build a prototype of this. We need to actually hash this out. We need something that the domain experts can
1:01:35
fiddle with. Oh, okay. We might need to integrate a a third party library into this. We might need to do some research.
1:01:41
We might need to actually kind of like um ping this back and forth and find a third party service that we can get the
1:01:47
most out of. We might need to go back with the information that we gathered there to the idea phase. So all the way
1:01:53
up to the sort of PRD and the journey, that's something you need to involve your team with. That's something where
1:01:58
these assets are going to be shared and argued over and you're going to have requests for comment on them and that
1:02:04
that loop is going to just keep grinding and grinding until you figure out where you're going. Once you figure out where
1:02:10
you're going, then you can start doing the came on board the implementation. But this is essentially super arguable
1:02:15
and the you'll be bouncing back and forth between the phases. Does that make sense? Yeah. Would you not need a PR for your
1:02:22
prototype? Say it again. Sorry. Would you not want to have a PR for your prototype? The question was, do you want
1:02:27
to go through this whole session just to sort of create a prototype? Do you not need a PRD for your prototype as well?
1:02:32
Let's just quickly talk about prototypes for a second. Um, there was a question about how do you make this work for front end?
1:02:39
Like how do you because front end is like really sensitive to human eyes. You need human eyes looking at the front end
1:02:45
all the time to make sure that it looks good. AI doesn't really have any eyes.
1:02:50
It can look at code, but it front end is multimodal. And so my experiences with
1:02:57
trying to plug AI into um let's say agent browser or playright MCP to give
1:03:03
it you can give it tools to allow it to look through a front end and sort of look at images but in my experience the
1:03:10
um it's not very good at that yet and it can't create a nice front end in a mature codebase. It can sort of spit one
1:03:17
out. But what it can do is you say okay uh I want some ideas on how uh this
1:03:22
front end might look. give me three prototypes um that I can click between in a throwaway uh throwaway route that I
1:03:30
can decide which one looks best and you take the asset of that prototype and you then feed it back into the grilling
1:03:36
session or you get feedback on it blah blah blah blah blah answer your question kind of thing the prototype is just you
1:03:42
know it's messy it's supposed to give you feedback early on in the process so that's a great way of working with front
1:03:47
end code great way of looking at software architecture in general let's go one more question yeah yes [clears throat] in your system How
1:03:53
do you integrate respecting an architecture a design with API contracts
1:03:59
and fitting with a larger system security constraints? All kinds of conraints like that.
1:04:04
Yeah, there's a lot in that question. The question was how do you conform with existing architecture? How do you do um
1:04:12
how do you make it conform to the code standards like of your codebase or Yeah. architecture design API security
1:04:19
rules that constraints your designs. Yeah. I'm going to answer that in a bit if
1:04:25
that's okay. So hopefully we have started to get some stuff cooking.
1:04:31
It's just pinging on the explore phase here.
1:04:37
Tempted to just start running it AFK. Maybe I will, maybe I won't. Um, what
1:04:44
it's essentially doing is it's exploring the repo. It's going to then start implementing based on what we wanted. Let's actually have one more question
1:04:50
just while it's running. Yeah.
1:04:58
Yeah. So the question was why do you not get AI to QA?
1:05:05
AI to QA. I just got jargon overload for a second. Um why do you not get AI to uh
1:05:11
test its own code? Now of course you absolutely can. And I think while it's doing while it's cooking here, okay,
1:05:18
it's got a clear picture of the codebase. It's assessing the issues. It's doing issue O2 is the next task.
1:05:24
I'm again going to show you that in a bit. I think the sort of uh because you definitely should do an automated review
Phase 6: Human-in-the-Loop Review
1:05:31
step as part of implementation. So you have your implementation. You should then because tokens are pretty cheap and
1:05:37
AI is actually really good at reviewing stuff. You should get it to review its own code before you then QA it. I found
1:05:43
that that catches a ton of different bugs. And the way that works is I will just do a
1:05:50
little diagram is if you have let's say an implementation that's sort of like used up a bunch of tokens in the smart
1:05:56
zone. If you get it to sort of try to do its reviewing, it's going to be doing
1:06:02
the reviewing in the dumb zone. And so the reviewer will be dumber than the
1:06:07
thing that actually implemented it. If we imagine this is the uh let's be consistent, that's the review. That's
1:06:14
the implementation. Whereas, if you clear the context,
1:06:19
then you're essentially going to be able to just review in the smart zone, which is where you want to be.
1:06:27
Let's see how our implementation is doing. Okay, good. It's generating a migration. That looks pretty nice. We're
1:06:33
getting some code spitting out. And while I'm sort of like, aha, here we
1:06:41
go. TDD. Let's talk about TDD and then I think we'll have a little another little
1:06:47
break. TDD I found is absolutely essential for getting the most out of
1:06:52
agents. Uh raise your hand if uh you know what TDD is. Cool. Okay. TDD is
1:06:58
testdriven development. What it's essentially doing is it's doing a something called red green refactor. And
1:07:04
if you look in the codebase, you'll be able to find a um a skill which really
1:07:09
describes how to do red green refactor. and teaches the AI how to do it. So what
1:07:14
it's doing is it's writing a failing test first. So it's saying, okay, I've broken down the idea of what I'm doing
1:07:21
and I'm just going to write a single test that fails and then I need to make the implementation pass. I have found
1:07:29
that first of all, this adds tests to the codebase and this this tends to add good tests to the codebase. And so we've
1:07:36
got this kind of gamification service. It looks like it's using some existing
1:07:41
stuff to create a test database. Test fails because the module doesn't exist yet. Okay, we've confirmed red. And then
1:07:47
it goes and hopefully runs it and it passes. I found that uh raise your hand
1:07:54
if you've ever had AI write bad tests. Yeah, it tends to try to cheat at the
1:08:00
tests because it's sort of doing it in layers. it will do the entire implementation and then it will do the
1:08:06
entire test layer just below it. Uh I'm just going to say yes, you're allowed to use npxv text. And using this technique,
1:08:14
it generally is a lot harder to cheat because it's sort of instrumenting the
1:08:21
code before it's then writing the code. So I find that TDD is so so good for
1:08:27
places where you can pull it off. And in fact, it's so good that I sort of warp my whole uh technique around getting TDD
1:08:34
to work better. I can see some drooping eyes. It is so hot in here. You can imagine how hot it is up here. Let's
1:08:40
take another five minute comfort break. Let's come back at quarter two. I think
1:08:46
have a nice generous one. And we'll be back in about six, seven minutes and I'll talk about how uh I think about
1:08:53
modules, think about constructing a codebase to make this possible. I've just been sort of fiddling with the AI
1:08:59
here and we have end up with some with a commit. So we have something to test.
1:09:04
Issue number two is complete. Here's what was done. This is kind of what it looks like when a Ralph loop completes
1:09:10
is you end up with a little summary. Um and we have now something we can QA
1:09:15
because we did the feedback loops or because we did the tracer bullets because we were uh said okay give us
1:09:21
something reviewable at the end of this we can immediately go and QA it. Now, there's nothing uh less exciting than
1:09:26
watching someone else QA something, but hopefully we can have a little play. Let's just check that it uh works at
1:09:33
all. In fact, before I go there, I just want to sort of work through what just
1:09:38
happened, which is we see that it's created some stuff on the dashboard
1:09:45
and it then ran the feedback loops. So, it then ran the tests and the types.
1:09:51
Now TDD is obviously really important and it's really important because these feedback loops are essential to AI
1:09:59
essential to get AI to produce anything reasonable because without this AI is totally coding blind right you have to
1:10:07
have to um if if your codebase doesn't have feedback loops you're never ever
1:10:13
ever going to get decent AI decent output out of AI and often what you'll find is that the quality of your
1:10:20
feedback back loops influences how good your AI can code. Essentially, that is the ceiling. So, if you're getting bad
1:10:27
outputs from your AI, you often need to increase the quality of your feedback loops. We'll talk about how to do that
1:10:33
in a minute. Now, so it ran uh npm run test, npm ran
1:10:39
type check. It got one type error and it needed to fix it with a nice bit of TypeScript magic. Very good. Yeah. Typo
1:10:46
level thresholds number. Okay. You see why I stopped teaching Typescript because just AI knows
1:10:51
everything now. Um, so and it ran the tests and it passed
1:10:57
and it's looking good. So we now end up with 284 tests in this repo. Pretty good.
1:11:03
I I do find uh front end really hard to test here. We're essentially just testing the service. So we've created a
1:11:10
gamification service if we look up here and then we have a test for that service. You can see the the service and
1:11:16
the test itself. Now, if I was doing code review here, I would then go to re I would first go to review the tests,
1:11:22
make sure the tests were testing reasonable things and then go and kind of review the code itself just to make
1:11:29
sure that it's it's not doing anything too crazy, right? The essential thing is I need to actually um look at the
1:11:35
dashboard. I'm going to log in as a student. Oh, if it'll let me. Maybe it
1:11:41
won't let me. Come on, son. There we go. Let's log in as Emma Wilson. Head into
1:11:47
courses. Uh, let's say I've got an introduction to TypeScript. Continue learning.
1:11:54
Uh, yes, I completed this lesson. Something went wrong. I imagine it's because I don't have
1:12:02
uh SQLite error. I don't have the right table. So, I need a table point events.
1:12:08
Point events is a strange table name. I'm not sure quite what it was thinking there. Uh, let's suspend. Let's run uh
1:12:14
npmdb migrate or push, I think.
1:12:19
Can't remember which one it was, but you kind of get the idea, right? I I'm not going to subject you to uh watching me
1:12:25
do QA because it's so dull. Um but at this point, I would essentially go back in. I would um let me open the project
1:12:33
back up. Uh, and I would this this is a crucial
1:12:38
moment. Um, and it's so important to um QA it manually here because QA Oh dear.
1:12:45
Oh dear. What's going wrong? There we go. QA is how I then um impose my
1:12:51
uh opinions back onto the codebase, how I impose my taste. What you'll often find is that um there are teams out
1:12:59
there who are trying to automate everything like every part of this process and they will tend to
1:13:06
uh if you try to like automate the sort of creation of the idea, automate uh the
1:13:11
QA, automate the research, automate the prototype, you end up with uh apps that I feel just lack taste and are bad.
1:13:22
maybe they just don't work or they they don't even work as intended or there's just no AI. You need a human touch when
1:13:28
you're building this stuff because without that you just end up with slop and we are not producing slop here.
1:13:33
We're trying to produce high quality stuff and so that's what the QA is for.
1:13:39
So I'm going to do two things in this final section which is I'm going to first tell you how to
1:13:46
there's probably a question in your mind here which is let's say I have a codebase that I'm working on and it's a
1:13:53
bad codebase. It's a codebase that's like really complicated uh that AI just
1:13:58
never does good work in and maybe actually most humans that go into that codebase don't do good work. How what
1:14:04
how do I improve that codebase? And the second thing is I'll show you my setup for parallelization.
1:14:10
So let's go with um bad code first. Now where is it? Where's the diagram?
1:14:17
Here it is. In his book um the philosophy of software design, John Alistster talks
1:14:24
about the ideal type of module. And let's imagine that you have a
1:14:30
codebase that looks like this. Each of these uh blocks here are individual files. And these files export things
1:14:37
from them. You know, they have um things that you pull from the files that you then use in other things. And so you
1:14:42
might have these weird dependencies where this file over here might rely on this file or might rely on that file for
1:14:48
instance. Now, if these files are small and they don't kind of ex like export
1:14:54
many things, then John would call these shallow modules essentially where they're not very um they kind of look
1:15:02
like uh this. If I actually no I can't can't make a good diagram of it. They're
1:15:08
essentially lots and lots of small chunks. Now this is hard for the AI to navigate because it doesn't really
1:15:14
understand the dependencies between everything. It can't work out where everything is. You know it has to sort of manually track through the entire
1:15:20
graph and go okay this relies on this one relies on this one. This one relies on this one.
1:15:26
And it's then also hard to test this as well because where do you draw your test boundaries here? Do you test each module
1:15:32
individually? Like just literally draw a test boundary. No, don't do that. Around this
1:15:39
one and then maybe another test boundary around the next one and then the next one
1:15:46
or should you sort of do big groups of it? Should you say, okay, we're going to test all of these related modules
1:15:51
together and just sort of, you know, hope and pray that they work.
1:15:57
Now [sighs] this means that if I think that bad tests mostly look like that
1:16:03
where the AI essentially tries to sort of wrap every tiny function in its own test boundary and then just sort of test
1:16:10
that those individually work. But what that does is it means that when let's say this module over here calls those
1:16:17
two. So it depends on both of these. Then this module might misorder the
1:16:23
functions or there might be sort of stuff inside that poor module that's worth testing on its own. And if you
1:16:29
then wrap this in a test boundary, what do you do? Do you mock the other two modules? How does that work?
1:16:37
So actually figuring out how to um build a codebase that is easy to test is
1:16:44
essential here because if our codebase is easy to test then our code our feedback loops are going to be better
1:16:50
and the AI is going to do better work in our codebase. Does that make sense? So what does a good codebase looks like?
1:16:56
Look like well not like that. It looks like this
1:17:02
where you have what John Asterhout calls deep modules. Modules that have a little interface on
1:17:10
there that expose a small simple interface that have a lot of functionality inside them. Now
1:17:18
what this means is that these are easy to test because you just let's say that there's a dependency between this one
1:17:23
and this one. My arrow working? Yeah, there we go.
1:17:29
Then what you do is you just wrap a big test boundary around that one module around
1:17:34
this one up here. And you're going to catch a lot of good stuff
1:17:40
because there's lots of functionality that you're testing and really the caller, the person calling the module is
1:17:46
going to have a simple interface to work from. So it's not not too tricky. That makes sense. Deep modules versus shallow
1:17:52
modules. This is good. This shallow version is bad. And what I find is that
1:17:58
unaided um or if you don't uh if you don't watch AI carefully, it's
1:18:06
going to produce a codebase that looks like this. So you need to be really really careful when you're directing it.
1:18:11
And that's why too is that if we look inside the PD, uh where is the PR gone? It's inside the
1:18:18
issues. It's inside the gamification system. Uh not found. Of course, it's not. Here it is.
1:18:25
Then I have uh inside here data model the modules.
1:18:32
So it's specifically saying okay this gamification service is a new deep module which we're going to test around.
1:18:38
It's going to have this particular interface and it's going to have um okay
1:18:44
we're modifying the progress service too. We're modifying the lesson route modifying the dashboard roots etc. So,
Phase 7: Deployment & Monitoring
1:18:50
it's I'm being really specific about the modules that I'm editing and I'm making sure that I keep that module map in my
1:18:56
mind at all times throughout the planning and then throughout the implementation. That make sense? Very,
1:19:02
very useful. It's useful for one other reason, too. Not only does it make your app more testable, but you get to do a
1:19:08
little mental trick. And I'm going to refill my water while you wait for what that is.
1:19:17
Uh, let me Let me get a question from you guys. So, raise your hands if you feel like.
1:19:26
Uh, if you feel like you're working harder than ever before with AI.
1:19:32
Yeah. Uh, raise your hands if you feel like you know your codebase less well
1:19:38
than you used to. Yeah. This is a real thing. um because we're
1:19:45
moving fast, because we're delegating more things, we end up losing a sense of our codebase. And if we lose the sense
1:19:52
of our codebase, we're not going to be able to improve it. And we're essentially delegating the shape of it
1:19:57
to AI. I [snorts] don't think that's good. But then how do we
1:20:03
how do we make it so that we can move fast while still keeping enough space in our brains? I think that this is a way
1:20:09
to do it because what you're doing here is not only are you thinking about
1:20:14
creating big shapes in your codebase, big services. What I think you should do is design the
1:20:22
interface for these modules, but then delegate the implementation. In other words, these modules can become
1:20:29
like gray boxes where you just need to know the shape of them. You need to know what they do and sort of how they
1:20:34
behave, but you can delegate the implementation of those modules. I found this is really nice. I don't necessarily
1:20:40
need to co-review everything inside that module. I don't necessarily need to know everything of what it's doing. I just
1:20:46
need to know that it behaves a certain way under certain conditions and that it does its thing. So, it's kind of like,
1:20:52
okay, I've got a big overview of my codebase and I understand kind of the shapes inside it, understand what the
1:20:57
interfaces all do, but I can delegate what's inside. I found that has been a
1:21:03
really nice way to retain my sense of the codebase while preserving my sanity.
1:21:08
Make sense? And so you might ask, how do I take a
1:21:14
codebase that looks like this and then turn it into a codebase that looks like
1:21:20
this? How do I deepen the modules? Well, we have hopefully it's in here. Pretty
1:21:25
sure it is. We have a skill and that skill is called improve codebase architecture.
1:21:32
Nice and direct. Uh let's run it. What this skill is
1:21:38
going to do is it's essentially just going to do a scan of our codebase and looking for what's available here. And
1:21:43
feel free to run this yourself if you're um uh running the exercises. And it's
1:21:49
exploring the architecture, exploring um essentially how to work within this codebase. and it's going to attempt to
1:21:57
uh find places to deepen the modules. Pretty simple. One really cool um thing
1:22:04
that it found here is part of my uh part of my course video manager app is a
1:22:09
video editor. A video editor built in the browser, which is really hardcore. Uh it's a decent bit of engineering. And
1:22:16
I wanted a way that I could wrap the entire front end all the way to the back end in like a single big module so that
1:22:23
I could test the fact that I press something on the front end and it goes all the way to the back end. And so I
1:22:28
found a way essentially by using a kind of discriminated union between the two types here by sort of I was able to use
1:22:35
this uh skill to essentially have a huge great big module that just tested from
1:22:41
the outside or was testable from the outside this video editor infrastructure. And it meant that AI
1:22:47
could see the entire flow, could act on the entire flow and test on the entire flow. And honestly, it was just night
1:22:53
and day in terms of the uh ability of AI to actually make changes because AI working on a video editor is pretty
1:22:59
brutal if you don't give it good tests. So that is honestly I if you take one
1:23:04
thing away from today, just try running this skill on your repo and see what happens. Let's go to slider. Let's ask a
1:23:11
uh check a couple of questions just while this is running. So let's see. Have you tried claude's
1:23:17
auto mode with claude enable auto mode? Uh that way you can avoid many of the obvious permission checks. We'll talk about permission checks in a second. Do
1:23:24
I keep the markdown plans and issues for later reference? Okay, this is a great question. So
1:23:34
let's say that you uh have a great idea, you turn it into a PR
1:23:40
raise and you then implement that PRD and the PRD is essentially done. Raise
1:23:45
your hand if you keep that information in the repo. So you turn it into a markdown file. Raise your hand if you
1:23:51
want to keep that around. Cool. Okay. And raise your hand if you if you don't want to keep it around. If
1:23:57
you want to get rid of it as soon as possible. Yeah. This is I think an a question that doesn't have a clear
1:24:03
answer. What I'm really scared of with any documentation decision is that
1:24:11
let's say that we have a PRD for this gamification system. We keep it in the repo. We go on, go on, go on. Let's say
1:24:17
a month later, we want some edits to the gamification system. And we go in with
1:24:22
Claude and it finds this old PR and says, "Yes, I found the original documentation for the PRD system." Well,
1:24:28
it turns out that the actual code has changed so much from the original PRD that it's almost unrecognizable. The
1:24:33
names of things have changed. The um file structure has changed. Even the requirements may have changed. We might have actually tested it with users. This
1:24:40
is dock rot where the documentation for something is rotting away in your repo
1:24:46
and influencing claude badly or claude agents badly. So I tend to not keep it
1:24:53
around. I tend to get rid of it. And for me because my setup uses GitHub issues,
1:24:58
I just mark it as closed. It can fetch it if it wants to, but it's got a visual indicator that it's done. So I tend to
1:25:03
prefer ditching these. Thoughts on the beads framework from
1:25:08
Steve? Uh I've not tested it, but it seems like sort of um another way to manage Canvan boards and issues. Seems
1:25:15
uh very good, but I've not tried it. Um
1:25:20
[clears throat] uh let me just quickly check the uh setup here. Let's take a couple of
1:25:27
questions from the room. Anybody got any questions at this point about anything that we've covered so far, especially this last bit? Yes.
1:25:40
like code. How about migrations? Like with migration files, we can also squash
1:25:45
them off like database migrations. Yeah,
1:25:51
I don't know. I hope that answers your question. I'm so sorry. No, no, I think database
1:25:56
migrations are a different thing because you have a sort of running record of exactly what changed and it's more deterministic and I think
1:26:04
yeah, it's an interesting analogy. I'm not sure. Let's talk about it afterwards. That's a good way of saying I have no
1:26:10
idea. Yeah. Yeah.
1:26:16
Sorry guys. Um I'm just trying to listen to this guy's question.
1:26:30
Yeah. The question the question here is um should I um in the sort of early
1:26:37
planning stage be trying to optimize the plan? This is something I actually see a lot of people doing and it's a really
1:26:43
good um idea. So when you
1:26:49
let's go back to the phases. So let's say that you have all of these phases here
1:26:55
and you uh you get to the point where you've sort of figured out everything with the LLM. you understand where
1:27:01
you're going. You've created this sort of journey destination document here. How do you then uh like should you then
1:27:09
try to optimize and optimize and optimize that PRD until it's the perfect PR you can possibly imagine? I don't
1:27:15
think there's a lot of value in that because I think the journey is really just sort of a hint of where you want to
1:27:22
go and the place that you need to be putting the work is in QA and you can sort of do that AFK I suppose but in my
1:27:29
experience you're not going to get a lot of juice out of it like it's the the thing that really matters is getting
1:27:34
alignment with the AI which is you do in the grilling session initially.
1:27:40
Let's have one more question. You got any more? Yeah. How do you get in your workflow to get it to code the way you
1:27:46
want it to code? So by the time you get to code review, it's at least familiar, use the libraries you wanted to use.
1:27:52
Yeah. Um, we had this question before actually, which was like uh how do you uh enforce your coding standards on the
1:27:59
agent? Essentially, how do you get it to code how you want it to code? Now, there's essentially two different ways
1:28:04
of doing it. Um, you've got Come on. Push
Designing Codebases for AI Effectiveness
1:28:11
and you've got pull. What do I mean by push and pull?
1:28:17
Um, push is where you push instructions to the LLM. So you say, okay, if you put
1:28:23
something in claw.md, uh, talk like a pirate, that instruction is always going to be sent to the agent,
1:28:30
right? So that is a push action. You're pushing tokens to it. Pull is where you
1:28:35
give the agent an opportunity to pull more information. And
1:28:42
that's for instance like skills. So a skill is something that can sit in the repo and it has a little description
1:28:47
header that says okay agent you may pull this when you want to.
1:28:53
My thinking my current thinking about code review and about coding standards looks like this. when you have an
1:29:00
implement. What's going on? There we go. Implementer.
1:29:06
I'm going to make this less red in a second. Um, then you want the coding
1:29:12
standards to be available via pull. If it has a question, you want it to be able to sort of answer it. But if you
1:29:18
then have an automated reviewer afterwards, then you want it to push.
1:29:24
You want to push that information to the reviewer. You want to say, "These are our coding standards." um make sure that
1:29:29
this code um follows them. So if you have skills for instance, then you want to push that stuff to the reviewer so
1:29:36
the reviewer has both the code that's written and the coding standards to compare to.
1:29:42
Hopefully that answers your question. I can show you an automated version of this as well. Actually, um yeah, let's
1:29:47
do that now just while it's fresh in my mind. I recently um spent
1:29:54
uh maybe a week or so uh building this thing called Sand Castle. And Sand
1:29:59
Castle is a I was sort of unhappy with the options out there for
1:30:05
um running agents AFK. And what this does is it's essentially a TypeScript library for running these loops. So you
1:30:12
have uh a run function that creates a work tree um sandboxes it in a docker
1:30:19
container and then allows you to run a prompt inside there. And in that work
1:30:24
tree then it's just a git branch and you have that code and you can then merge it later. If I open up
1:30:32
um there are some really really nice ways of viewing this and it essentially allows you to run these kind of
1:30:38
automated loops and allows you to parallelize across multiple different agents really simply. So I'll go into my
1:30:46
sand castle file go into main.ts here and let's just walk through this.
1:30:51
So this is kind of like I showed you um a sort of version of the Ralph loop earlier. This is where we take it from
1:30:58
sequential into parallel. We have here first of all a planner that
1:31:04
takes in it's has a plan prompt here that looks at the backlog and chooses a
1:31:10
certain number of issues to work on in parallel. Remember I showed you that canon board where it had all the blocking relationships. It works out all
1:31:16
of the phases. So this one will say okay uh let's say we have uh you can ignore
1:31:21
all this glue code here. This is essentially just a set of issues, GitHub issues with a title and with a a branch
1:31:30
for you to work on. And then for each issue, we create a sandbox
1:31:38
and then we run an implement in that sandbox passing in the issue number, issue title and the branch. This is like
1:31:43
the loop that we ran just before. Then if it created some commits, we then
1:31:49
review those commits. This is essentially the loop. What do we do with those commits? We pass those into a
1:31:58
merger agent which takes in a merge prompt, takes in the branches that were created, takes in
1:32:04
the issues, and it just merges them in. If there are any issues with the merge, you know, with the types and tests and that kind of thing, it solves them. And
1:32:11
this has been my uh flow for quite a while now for working on most projects. It works super super well. And uh yeah,
1:32:19
I recommend you check out sand castle if you want to sort of learn more. And to answer your question properly is that in
1:32:26
the reviewer uh I would push the coding standards in the implement I would allow it to pull.
1:32:33
And I'm actually using uh sonet for implementation and opus for um reviewing
1:32:39
because I consider reviewing sort of I need I need the smarts. Then
1:32:44
any question? Actually, let let me uh before we do more questions, let's go back here. Okay, where are we at? Okay,
1:32:53
we're sort of zooming everywhere in this uh talk because I'm kind of having to run things in parallel. So, let's go back to the improved codebase
1:33:00
architecture. It has finally finished running and it's found a bunch of architectural improvement candidates. So
1:33:06
it's got essentially a cluster of different modules that are all kind of related that could probably be tested as
1:33:12
a unit. Got number one the quiz scoring service. There's some reordering logic extraction as well. It has arguments for
1:33:20
why they're coupled and it has a dependency category as well. So local substitutable in SQLite within memory
1:33:26
test DB quiz scoring service currently has zero test. This is the biggest gap. So this
1:33:32
is what it looks like when we come back of uh improved codebase architecture.
1:33:37
Okay. So we have nominally kind of 17 minutes
1:33:43
left. I don't know about you, but I'm knackered. [laughter] Um I want to
1:33:49
[clears throat] let let me kind of sum up for you because I think we're sort of reaching
1:33:54
the end of our stamina. I'm going to be available for the full time if you want to um come and ask me questions. Um, I might do one more check of the slider,
1:34:00
but let's kind of sum up where we've got to. So,
Final Takeaways & Summary
1:34:06
this is essentially the flow where throughout this whole process,
1:34:12
we're bearing in mind the shape of our codebase. This is not a specttocode compiler. This is not an AI that's sort
1:34:19
of just like churning out code. We are being very intentional with the kind of modules and the shape of the codebase
1:34:24
that we want. We are making sure that we are as aligned as possible by using the grilling session by really hammering out
1:34:31
our idea. We're not overindexing into the PRD. We're not trying to read every part of it. We're not thinking too much
1:34:37
about it even. We're then just turning that into a set of parallelizable issues which can be worked on by agents in
1:34:42
parallel. We implement it and we QA and code review the hell out of it and then
1:34:48
keep going back to that implementation. One thing I didn't really mention is that in the QA phase, what the QA phase
1:34:54
is for is creating more issues for that canon board. So while it's implementing even, you can be QAing the stuff and
1:35:00
going back adding more issues. And the canon board just allows you to add blocking issues kind of um sort of
1:35:06
infinitely really. And then once that's all done, once you've got code that you're happy with, once you've got work that you're happy with, then you can
1:35:12
share it with your team and you can get a full review. So this is kind of like once you get here, this is kind of one
1:35:17
developer or maybe a couple of developers sort of managing this and then it's kind of up to you to figure out how to merge it back in.
1:35:25
[sighs] Of course, all of this can be customized
1:35:30
by you. This is just something that I have found works. I'm not trying to like sell you on a kind of approach here.
1:35:37
What I recommend if you take one thing away from this session is that you should head back you should head to
1:35:42
Amazon and just buy a ton of those old books because I mean I just found it so
1:35:47
enlightening reading them. Uh you know preai writing is always like a really
1:35:53
fun to read anyway and I just on every single page I found that
1:35:58
there was something useful and something interesting to to read. So thank you so much. Thank you for putting up with the
1:36:04
heat. Um hopefully your body temperatures will reset soon. Uh thank you very much. [applause]
1:36:23
[music]

