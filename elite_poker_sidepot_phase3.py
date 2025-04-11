import streamlit as st
import random
import matplotlib.pyplot as plt
import time

chip_denominations = [100, 500, 1000, 2500]
chip_colors = {100: "red", 500: "blue", 1000: "green", 2500: "purple"}
players = [chr(65 + i) for i in range(5)]  # A–E

# --- UTILITIES ---
def generate_unique_stacks():
    stacks = set()
    while len(stacks) < 5:
        stacks.add(sum(random.choices(chip_denominations, k=random.randint(1, 4))))
    return list(sorted(stacks))

def assign_all_in_players():
    stacks = generate_unique_stacks()
    assignments = dict(zip(players, stacks))
    all_in_count = random.choice([2, 3, 4])
    all_ins = random.sample(players, all_in_count)
    return assignments, all_ins

def calculate_side_pots(assignments, all_ins):
    eligible = {p: assignments[p] for p in all_ins}
    sorted_players = sorted(eligible.items(), key=lambda x: x[1])
    pots = []
    prev_amt = 0
    for i, (player, amt) in enumerate(sorted_players):
        if amt > prev_amt:
            group = sorted_players[i:]
            portion = amt - prev_amt
            eligible_players = [p[0] for p in group]
            if len(eligible_players) > 1:
                pots.append({
                    "Name": "Main Pot" if len(pots) == 0 else f"Side Pot #{len(pots)}",
                    "Amount": portion * len(group),
                    "Eligible Players": eligible_players
                })
            prev_amt = amt
    max_stack = max(eligible.items(), key=lambda x: x[1])
    refund = max_stack[1] - max([v for k, v in eligible.items() if k != max_stack[0]])
    return pots, max_stack[0], max(0, refund)

def break_into_chips(amount):
    chips = []
    for value in sorted(chip_denominations, reverse=True):
        while amount >= value:
            chips.append(value)
            amount -= value
    return chips

def draw_pots(pots):
    fig, ax = plt.subplots(figsize=(10, len(pots)))
    y_step = 1.5
    for idx, pot in enumerate(reversed(pots)):
        y = idx * y_step
        chips = break_into_chips(pot["Amount"])
        x = 0
        for chip in chips:
            circ = plt.Circle((x, y), 0.3, color=chip_colors[chip], ec='black')
            ax.add_patch(circ)
            ax.text(x, y, str(chip), color='white', fontsize=8, ha='center', va='center')
            x += 0.6
        ax.text(x + 0.5, y, f"{pot['Name']}: {pot['Amount']} chips", fontsize=10)
    ax.set_xlim(-1, 20)
    ax.set_ylim(-1, y_step * len(pots))
    ax.axis('off')
    st.pyplot(fig)

# --- STREAMLIT CONFIG ---
st.set_page_config(page_title="Elite Poker Sidepot Training and Quiz", layout="centered")
st.title("🏆 Elite Poker Sidepot Training and Quiz")

# --- SESSION STATE INIT ---
if "booted" not in st.session_state:
    st.session_state.booted = True
    st.session_state.mode = "Training"
    st.session_state.quiz_length = 10
    st.session_state.current_hand = 1
    st.session_state.score = 0
    st.session_state.streak = 0
    st.session_state.timer_on = False
    st.session_state.start_time = 0
    st.session_state.history = []
    st.session_state.step = "setup"

# --- SETUP SCREEN ---
if st.session_state.step == "setup":
    st.subheader("🛠️ Setup Your Session")
    st.session_state.mode = st.radio("Mode", ["Training", "Quiz"])
    st.session_state.quiz_length = st.radio("How many hands?", [10, 20, 30])
    st.session_state.timer_on = st.checkbox("Enable Timer?")
    if st.button("Start"):
        st.session_state.current_hand = 1
        st.session_state.score = 0
        st.session_state.streak = 0
        st.session_state.history = []
        st.session_state.step = "guess_pots"
        st.session_state.stacks, st.session_state.all_ins = assign_all_in_players()
        st.session_state.pots, st.session_state.big_stack, st.session_state.refund = calculate_side_pots(st.session_state.stacks, st.session_state.all_ins)
        st.session_state.guess = None
        st.session_state.pot_index = 0
        st.session_state.selection = []
        if st.session_state.timer_on:
            st.session_state.start_time = time.time()
        st.rerun()

# --- GAMEPLAY ---
if st.session_state.step != "setup":
    st.markdown(f"### Hand {st.session_state.current_hand} of {st.session_state.quiz_length}")
    st.subheader("Player Stacks")
    for p in sorted(st.session_state.stacks):
        st.markdown(f"- **{p}**: {st.session_state.stacks[p]} chips")
    st.markdown(f"🟩 **All-Ins**: {', '.join(st.session_state.all_ins)}")
    st.markdown(f"🔥 Streak: {st.session_state.streak}")
    if st.session_state.timer_on:
        elapsed = int(time.time() - st.session_state.start_time)
        st.markdown(f"⏱️ Time: {elapsed} seconds")

# --- POT COUNT GUESS ---
if st.session_state.step == "guess_pots":
    st.subheader("Step 1: How many pots?")
    guess_input = st.text_input("Total pots (main + side)?")
    if st.button("Submit Guess"):
        if guess_input.strip().isdigit():
            st.session_state.guess = int(guess_input.strip())
            st.session_state.step = "show_pots"
            st.rerun()
        else:
            st.warning("Enter a valid number!")

# --- SHOW POT BREAKDOWN ---
elif st.session_state.step == "show_pots":
    st.subheader("Step 2: Pot Breakdown")
    actual_pot_count = len(st.session_state.pots)
    st.markdown(f"📦 You guessed: **{st.session_state.guess}**")
    st.markdown(f"✅ Actual pots: **{actual_pot_count}**")
    draw_pots(st.session_state.pots)
    st.session_state.step = "eligibility"
    st.session_state.pot_index = 0
    st.session_state.selection = []
    st.rerun()

# --- ELIGIBILITY GUESS ---
elif st.session_state.step == "eligibility":
    pot = st.session_state.pots[st.session_state.pot_index]
    st.subheader(f"Step 3: Who is eligible for {pot['Name']}?")
    st.write(f"Pot Amount: **{pot['Amount']} chips**")

    col1, col2, col3, col4, col5 = st.columns(5)
    cols = [col1, col2, col3, col4, col5]
    for i, p in enumerate(players):
        button_label = f"✅ {p}" if p in st.session_state.selection else p
        if cols[i].button(button_label, key=f"btn_{p}_{st.session_state.pot_index}"):
            if p in st.session_state.selection:
                st.session_state.selection.remove(p)
            else:
                st.session_state.selection.append(p)
            st.rerun()

    st.markdown(f"🔘 Selected: {', '.join(st.session_state.selection)}")

    if st.button("Submit Selection"):
        correct = set(pot["Eligible Players"])
        guess = set(st.session_state.selection)
        result = guess == correct
        if result:
            st.success("✅ Correct!")
            st.session_state.score += 1
            st.session_state.streak += 1
        else:
            st.error(f"❌ Incorrect. Correct: {', '.join(correct)}")
            st.session_state.streak = 0

        st.session_state.history.append({
            "hand": st.session_state.current_hand,
            "pot": pot["Name"],
            "correct": correct,
            "guess": guess
        })

        if st.session_state.pot_index + 1 < len(st.session_state.pots):
            st.session_state.pot_index += 1
            st.session_state.selection = []
            st.rerun()
        else:
            st.session_state.step = "refund_guess"
            st.rerun()

# --- REFUND QUESTION ---
elif st.session_state.step == "refund_guess":
    st.subheader("Step 4: Excess Chips")
    refund_guess = st.text_input(f"How many chips go back to **{st.session_state.big_stack}** (largest stack)?")
    if st.button("Submit Refund Guess"):
        correct_refund = st.session_state.refund
        if refund_guess.strip().isdigit():
            if int(refund_guess.strip()) == correct_refund:
                st.success("✅ Correct!")
                st.session_state.score += 1
                st.session_state.streak += 1
            else:
                st.error(f"❌ Incorrect. Correct amount: {correct_refund}")
                st.session_state.streak = 0
        else:
            st.warning("Please enter a valid number.")

        if st.session_state.current_hand < st.session_state.quiz_length:
            st.session_state.current_hand += 1
            st.session_state.step = "guess_pots"
            st.session_state.stacks, st.session_state.all_ins = assign_all_in_players()
            st.session_state.pots, st.session_state.big_stack, st.session_state.refund = calculate_side_pots(st.session_state.stacks, st.session_state.all_ins)
            st.session_state.guess = None
            st.session_state.pot_index = 0
            st.session_state.selection = []
            st.rerun()
        else:
            st.session_state.step = "review"
            st.rerun()

# --- FINAL REVIEW ---
elif st.session_state.step == "review":
    st.header("🧠 Quiz Complete!")
    st.success(f"Final Score: {st.session_state.score} / {st.session_state.quiz_length * 2}")
    if st.session_state.timer_on:
        elapsed = int(time.time() - st.session_state.start_time)
        st.markdown(f"⏱️ Total Time: {elapsed} seconds")

    for item in st.session_state.history:
        result = "✅" if item["guess"] == item["correct"] else "❌"
        st.markdown(f"**Hand {item['hand']} - {item['pot']}**: {result}")
        st.markdown(f"- Your Guess: {', '.join(item['guess'])}")
        st.markdown(f"- Correct: {', '.join(item['correct'])}")
        st.markdown("---")

    if st.button("Play Again"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
