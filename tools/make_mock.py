# -*- coding: utf-8 -*-
"""生成一套原创六级模拟卷（2026 命题热点：AI + 传统文化 + 环保），
听力用 Windows TTS 合成，题目与答案写进 data/exam_mock.js。

跑法：python tools/make_mock.py
"""
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
AUDIO = os.path.join(DATA, "audio")
FF = "ffmpeg"

# ── 听力原文（原创） ─────────────────────────────────────────────
LISTENING = [
    ("Conversation 1", """W: You look exhausted, Marcus. Did the exhibition go badly?
M: Not badly, just endless. We spent two weeks designing the poster, and the client changed the headline three times on the last day.
W: That is the part nobody warns you about. When I worked at the design studio, the brief always sounded simple until the second meeting.
M: Exactly. And the strangest thing is that the final version is almost the one we proposed first.
W: So the two weeks were not wasted, then. You learned what the client actually wanted.
M: I keep telling myself that. Next time I will show two options in the first meeting and ask which one feels closer.
W: Do that. It turns a argument about words into a choice between pictures."""),
    ("Conversation 2", """M: Professor Lin, is it true that this year's translation task will focus on traditional culture again?
W: The topics rotate, but culture, technology and the environment keep coming back. What changes is the angle.
M: So a student who memorised thirty set phrases is not safe?
W: Not safe, no. Examiners can tell a memorised phrase from a sentence you actually built. The phrases help, but the sentence has to belong to the question.
M: Then how should I practise in the last month?
W: Translate one short paragraph every day, and read it aloud afterwards. If it sounds like Chinese word order in English, rewrite it.
M: And the vocabulary?
W: Learn words in pairs that contrast, like preserve and abandon, or temporary and permanent. Contrast is what examiners test."""),
]

PASSAGE_SCRIPT = 'Passage. Across Asia, universities are quietly turning old libraries into study commons.\nThe books stay, but the desks multiply, and the silence is replaced by a low hum of group work.\nSupporters say the change matches how students actually learn: in pairs, with laptops open, explaining a problem to each other.\nCritics worry that the reading room, one of the few places where thinking is done slowly, is disappearing.\nMost universities have settled on a compromise. The top floor keeps its silence and its wooden tables, while the ground floor is open, bright and noisy.\nStudents, it turns out, use both, and often on the same day.'

TALK_SCRIPT = 'Talk. Good morning. Today I want to talk about why so much advice about saving energy fails.\nThe advice is usually accurate. Turn off the lights, take shorter showers, unplug the charger. The problem is that none of it is visible.\nA person who turns off a light cannot see the power station that does not need to burn coal, so the action feels small and the reward never arrives.\nWhen a building installs meters in the lobby, and the number drops the week after a campaign, consumption falls by around eight percent, and it stays down.\nThe lesson is not that people are lazy. It is that feedback, not instruction, changes behaviour.'

# ── 题目（原创） ─────────────────────────────────────────────────
def q(n, stem, opts, ans):
    return {"t": "q", "n": n, "stem": stem, "opts": [[chr(65 + i), o] for i, o in enumerate(opts)], "ans": ans}


QUESTIONS = [
    q(1, "What does the man say about the exhibition?", [
        "It was cancelled at the last minute.",
        "It took far more time than expected.",
        "It attracted fewer visitors than planned.",
        "It was praised by the client."], "B"),
    q(2, "What does the woman say nobody warns designers about?", [
        "The client may change the brief repeatedly.",
        "The printing cost is usually underestimated.",
        "The first idea is rarely accepted.",
        "Designers often work alone."], "A"),
    q(3, "What does the man find strangest about the project?", [
        "The client refused to meet him.",
        "The final poster resembled his first proposal.",
        "The studio lost the contract.",
        "The headline was written by the client."], "B"),
    q(4, "What will the man do differently next time?", [
        "Charge a higher fee.",
        "Hire an assistant.",
        "Show two options at the first meeting.",
        "Refuse last minute changes."], "C"),

    q(5, "What topics keep returning in the translation task?", [
        "Culture, technology and the environment.",
        "Sports, travel and food.",
        "History, politics and law.",
        "Education, health and housing."], "A"),
    q(6, "Why are memorised phrases not enough?", [
        "They are often translated wrongly.",
        "Examiners can tell them from sentences built for the question.",
        "They take too long to recall.",
        "They are not accepted in the new format."], "B"),
    q(7, "What does the professor suggest practising daily?", [
        "Reciting thirty set phrases.",
        "Reading English newspapers aloud.",
        "Translating one short paragraph and reading it aloud.",
        "Writing two essays a week."], "C"),
    q(8, "Why does the professor recommend learning words in pairs?", [
        "Pairs are easier to memorise.",
        "Contrast is what examiners test.",
        "Pairs appear more often in reading.",
        "It reduces the number of words needed."], "B"),

    q(9, "What change are universities making to old libraries?", [
        "Closing them for renovation.",
        "Turning them into study commons.",
        "Moving them off campus.",
        "Replacing books with computers."], "B"),
    q(10, "What do supporters say about the change?", [
        "It matches how students actually learn.",
        "It saves money for the university.",
        "It improves the building's reputation.",
        "It attracts international students."], "A"),
    q(11, "What do critics worry about?", [
        "The loss of group discussion space.",
        "The cost of new furniture.",
        "The disappearance of slow, silent reading.",
        "The shortage of librarians."], "C"),
    q(12, "How have most universities settled the dispute?", [
        "By keeping silent floors and adding open ones.",
        "By banning laptops in the library.",
        "By building a new library.",
        "By renting space to cafes."], "A"),

    q(13, "Why does the speaker say energy advice often fails?", [
        "The advice is usually wrong.",
        "The results of saving are invisible.",
        "People do not care about the environment.",
        "The equipment is too expensive."], "B"),
    q(14, "What happens when meters are installed in the lobby?", [
        "Consumption rises slightly.",
        "Consumption falls and stays down.",
        "People ignore the meters.",
        "The building installs solar panels."], "B"),
    q(15, "What is the speaker's main point?", [
        "Instruction matters more than feedback.",
        "Feedback, not instruction, changes behaviour.",
        "Energy saving is mainly a technical problem.",
        "Campaigns should be shorter."], "B"),
]

READING_PASSAGE = """The Quiet Return of the Reading Room

For two decades, the university library was described as a service, and services are judged by how many people use them. Seats filled, doors stayed open late, and the building was counted successful. Then the counts stopped rising, and administrators looked for a new argument.

The argument they found was learning. Studies of student behaviour kept reporting the same thing: the most effective study sessions were short, social and repetitive, a pair of students explaining a problem to each other until it made sense. A reading room built for silence was, by that measure, the wrong shape.

So the buildings changed. Ground floors were opened up, whiteboards appeared, and coffee arrived. The changes were popular, and they were also cheap to explain to a committee.

What the committees did not anticipate was the second effect. Once the noisy floor existed, the silent floor became a choice rather than a rule, and students began to protect it. Sign-up sheets appeared at exam time. Librarians reported that the top floor, once half empty on a Tuesday afternoon, was now full by ten in the morning.

The reading room had not been obsolete. It had been undefended. Given a reason to exist alongside the group work rather than in competition with it, it filled.

That is an uncomfortable lesson for institutions that measure only use. A space can be valuable precisely because it is not busy all the time, the way a pause is valuable in a sentence. Counting cannot see the difference, and so the counting has to be supplemented by judgement, which is harder to table at a meeting."""

READING_Q = [
    q(16, "How was the library judged for two decades?", [
        "By the quality of its collections.",
        "By how many people used it.",
        "By the number of staff employed.",
        "By its opening hours."], "B"),
    q(17, "What did studies of student behaviour report?", [
        "Long silent sessions worked best.",
        "Effective study was short, social and repetitive.",
        "Students preferred studying alone at night.",
        "Group work reduced exam results."], "B"),
    q(18, "What happened to the silent floor after the changes?", [
        "It was closed for lack of use.",
        "It became a choice students protected.",
        "It was turned into a coffee shop.",
        "It was used only by librarians."], "B"),
    q(19, "What does the writer mean by 'It had been undefended'?", [
        "The room had no security.",
        "Nobody had argued for its value.",
        "The building was poorly maintained.",
        "The collection was incomplete."], "B"),
    q(20, "What is the writer's conclusion about counting?", [
        "Counting is the only reliable measure.",
        "Counting must be supplemented by judgement.",
        "Counting should be abandoned.",
        "Counting works for libraries but not classrooms."], "B"),
]

TRANSLATION_PROMPT = "人工智能正在改变中国的教育。许多学校用智能系统批改作业，帮助老师了解每个学生的薄弱环节。学生也可以通过在线平台向远方的老师提问。有人担心技术会让学生变懒，但更多人认为，机器负责重复劳动，人负责思考和判断，两者结合才能提高教学质量。"
TRANSLATION_REF = ("Artificial intelligence is changing education in China. Many schools use intelligent systems to grade "
                   "homework and help teachers identify each student's weak points. Students can also ask teachers far away "
                   "questions through online platforms. Some worry that technology will make students lazy, but more people "
                   "believe that machines should handle repetitive work while people do the thinking and judging, and that "
                   "only by combining the two can teaching quality improve.")

WRITING_PROMPT = ("For this part, you are allowed 30 minutes to write an essay on how college students should use AI tools "
                  "in their study. You should write at least 150 words but no more than 200 words.")

PARTS = [
    {"name": "Part I Writing", "blocks": [
        {"t": "p", "x": "Directions: " + WRITING_PROMPT},
        {"t": "p", "x": "参考思路：先承认工具的价值（查资料、改语法），再提出边界（不能代写、不能代替思考），最后给一个具体做法（先自己写，再用工具检查）。"},
    ]},
    {"name": "Part II Listening Comprehension", "blocks": [
        {"t": "h", "x": "Section A · Conversations"},
        {"t": "p", "x": "听两段对话，回答 1–8 题。"},
    ] + [b for b in QUESTIONS[:8]] + [
        {"t": "h", "x": "Section B · Passage"},
        {"t": "p", "x": "听一篇短文，回答 9–12 题。"},
    ] + QUESTIONS[8:12] + [
        {"t": "h", "x": "Section C · Talk"},
        {"t": "p", "x": "听一段讲话，回答 13–15 题。"},
    ] + QUESTIONS[12:15]},
    {"name": "Part III Reading Comprehension", "blocks": [
        {"t": "p", "x": READING_PASSAGE},
    ] + READING_Q},
    {"name": "Part IV Translation", "blocks": [
        {"t": "p", "x": "Directions: 将下面这段中文译成英文。"},
        {"t": "p", "x": TRANSLATION_PROMPT},
        {"t": "p", "x": "参考译文：" + TRANSLATION_REF},
    ]},
]


def tts(text, out_wav):
    """用 SAPI 的英文声音合成语音。"""
    tmp = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8")
    tmp.write(text)
    tmp.close()
    ps = f'''
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.SelectVoice('Microsoft Zira Desktop')
$s.Rate = -1
$t = Get-Content -Raw -LiteralPath '{tmp.name}'
$s.SetOutputToWaveFile('{out_wav}')
$s.Speak($t)
$s.Dispose()
'''
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=False, capture_output=True)
    os.unlink(tmp.name)


def main():
    os.makedirs(AUDIO, exist_ok=True)
    script = "\n\n".join(
        [f"{name}.\n{body}" for name, body in LISTENING] + [PASSAGE_SCRIPT, TALK_SCRIPT]
    )
    wav = os.path.join(AUDIO, ".mock.wav")
    mp3 = os.path.join(AUDIO, "mock_cet6_listening.mp3")
    print("TTS...", flush=True)
    tts(script, wav)
    print("wav", os.path.getsize(wav) // 1024, "KB")
    subprocess.run([FF, "-y", "-loglevel", "error", "-i", wav, "-ac", "1", "-ar", "24000",
                    "-b:a", "48k", mp3], check=False)
    os.remove(wav)
    print("mp3", os.path.getsize(mp3) // 1024, "KB")

    data = {
        "key": "mock",
        "title": "六级 · 原创模拟卷（AI 与教育）",
        "level": "cet6",
        "session": "mock",
        "audio": "data/audio/mock_cet6_listening.mp3",
        "parts": PARTS,
        "answers": {str(x["n"]): x["ans"] for x in QUESTIONS + READING_Q},
        "explanations": {},
    }
    out = os.path.join(DATA, "exam_mock.js")
    with open(out, "w", encoding="utf-8") as f:
        f.write("window.DATA_EXAM=" + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n")
    print("questions", len(QUESTIONS), "size", os.path.getsize(out) // 1024, "KB")


if __name__ == "__main__":
    main()
