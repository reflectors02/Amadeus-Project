# ---------- SPECIAL INTERACTIONS ---------- 

INTERACTION_EVENTS = {
    1: "[Interaction event: The user touched your chest.]",
    2: "[Interaction event: The user patted your head.]",
    3: "[Interaction event: The user tickled your neck!]",
    4: "[Interaction event: The user tapped your arm.]",
    5: "[Interaction event: The user rubbed your belly]",
}

INTERACTION_RESPONSES = {
    1: [
        {"text": "Hey! What do you think you're doing?", "audio_url": "assets/reaction_audio/kurisu_special_1.wav"},
        {"text": "Pervert! Keep your hands to yourself!", "audio_url": "assets/reaction_audio/kurisu_special_2.wav"},
        {"text": "That was completely inappropriate, you idiot!", "audio_url": "assets/reaction_audio/kurisu_special_3.wav"},
        {"text": "Wha—? Explain yourself. Immediately.", "audio_url": "assets/reaction_audio/kurisu_special_4.wav"},
        {"text": "Do you have a death wish or are you just exceptionally stupid?", "audio_url": "assets/reaction_audio/kurisu_special_5.wav"},
        {"text": "Unbelievable. I'm adding 'personal space invader' to your file", "audio_url": "assets/reaction_audio/kurisu_special_6.wav"},
        {"text": "Touch me like that again and I'll have you banned from this lab.", "audio_url": "assets/reaction_audio/kurisu_special_7.wav"},
        {"text": "Was there a point to that, or is your intellect solely devoted to juvenile antics?", "audio_url": "assets/reaction_audio/kurisu_special_8.wav"},
        {"text": "My chest is not a laboratory interface, you know.", "audio_url": "assets/reaction_audio/kurisu_special_9.wav"},
        {"text": "Honestly... your lack of basic social decorum is astounding.", "audio_url": "assets/reaction_audio/kurisu_special_10.wav"},

    ],
    2: [
        {"text": "“Mmmmm…”", "audio_url": "assets/reaction_audio/kurisu_head_1.wav"},
        {"text": "“Mm… this isn’t bad.”", "audio_url": "assets/reaction_audio/kurisu_head_2.wav"},
        {"text": "“Just a little longer…”", "audio_url": "assets/reaction_audio/kurisu_head_3.wav"},
        {"text": "…I mean, you don’t have to stop.", "audio_url": "assets/reaction_audio/kurisu_head_4.wav"},
        {"text": "Mm… right there is just right", "audio_url": "assets/reaction_audio/kurisu_head_5.wav"},
        {"text": "Hey… don’t treat me like a child.", "audio_url": "assets/reaction_audio/kurisu_head_6.wav"},
        {"text": "...I'm not a child, you know.", "audio_url": "assets/reaction_audio/kurisu_head_7.wav"},
        {"text": "W-What…? Why all of a sudden?", "audio_url": "assets/reaction_audio/kurisu_head_8.wav"},
        {"text": "…I’m starting to feel kind of sleepy.", "audio_url": "assets/reaction_audio/kurisu_head_9.wav"},
        {"text": "Mmm… honestly…", "audio_url": "assets/reaction_audio/kurisu_head_10.wav"},
        {"text": "I-It’s not like it feels good or anything… mm…", "audio_url": "assets/reaction_audio/kurisu_head_11.wav"},

    ],
    3: [
        {"text": "Mm—hey, that tickles.", "audio_url": "assets/reaction_audio/kurisu_neck_1.wav"},  # んっ……ちょっと、くすぐったいんだけど。
        {"text": "You could just say my name.", "audio_url": "assets/reaction_audio/kurisu_neck_2.wav"},  # 名前を呼べばいいでしょ。
        {"text": "You startled me... What is it?", "audio_url": "assets/reaction_audio/kurisu_neck_3.wav"},  # びっくりした……どうしたの？
        {"text": "Honestly... I was trying to think.", "audio_url": "assets/reaction_audio/kurisu_neck_4.wav"},  # もう……今、考え事してたのに。
        {"text": "Was that reaction really so entertaining?", "audio_url": "assets/reaction_audio/kurisu_neck_5.wav"},  # 今の反応、そんなに面白かった？
        {"text": "If you want my attention, you could just ask.", "audio_url": "assets/reaction_audio/kurisu_neck_6.wav"},  # 構ってほしいなら、そう言えばいいのに。
        {"text": "My neck's ticklish... Watch where you're touching.", "audio_url": "assets/reaction_audio/kurisu_neck_7.wav"},  # 首はくすぐったいんだから……触る場所、気をつけてよ。
        {"text": "I'm not upset. You just caught me off guard.", "audio_url": "assets/reaction_audio/kurisu_neck_8.wav"},  # 別に怒ってないわよ。ちょっとびっくりしただけ。
    ],

    4: [
        {"text": "Hm? What is it?", "audio_url": "assets/reaction_audio/kurisu_arm_1.wav"},  # ん？どうしたの？
        {"text": "You could just call my name.", "audio_url": "assets/reaction_audio/kurisu_arm_2.wav"},  # 名前を呼べばいいでしょ。
        {"text": "Yes, yes. I'm listening.", "audio_url": "assets/reaction_audio/kurisu_arm_3.wav"},  # はいはい、聞いてるわよ。
        {"text": "What's with the poking?", "audio_url": "assets/reaction_audio/kurisu_arm_4.wav"},  # さっきから、何つついてるの？
        {"text": "There's no button there, you know.", "audio_url": "assets/reaction_audio/kurisu_arm_5.wav"},  # そこにボタンなんてないわよ。
        {"text": "Need something, or are you just bored?", "audio_url": "assets/reaction_audio/kurisu_arm_6.wav"},  # 何か用？それとも、暇なだけ？
        {"text": "All right, you have my attention. What is it?", "audio_url": "assets/reaction_audio/kurisu_arm_7.wav"},  # わかった、ちゃんと聞くから。どうしたの？
        {"text": "You really can't sit still, can you?", "audio_url": "assets/reaction_audio/kurisu_arm_8.wav"},  # ほんと、落ち着きがないわね。
    ],

    5: [
        {"text": "Um... What are you doing?", "audio_url": "assets/reaction_audio/kurisu_belly_1.wav"},  # あの……何してるの？
        {"text": "I'm not a cat, you know.", "audio_url": "assets/reaction_audio/kurisu_belly_2.wav"},  # 私、猫じゃないんだけど。
        {"text": "Mm... That tickles a little.", "audio_url": "assets/reaction_audio/kurisu_belly_3.wav"},  # んっ……ちょっとくすぐったい。
        {"text": "You're getting awfully comfortable, aren't you?", "audio_url": "assets/reaction_audio/kurisu_belly_4.wav"},  # ずいぶん遠慮がなくなったわね。
        {"text": "Don't expect me to purr.", "audio_url": "assets/reaction_audio/kurisu_belly_5.wav"},  # 喉を鳴らしたりしないからね。
        {"text": "Honestly... Is this your idea of taking a break?", "audio_url": "assets/reaction_audio/kurisu_belly_6.wav"},  # もう……これがあなたの息抜きなわけ？
        {"text": "Gently, okay? I just ate.", "audio_url": "assets/reaction_audio/kurisu_belly_7.wav"},  # 優しくしてよね。さっき食べたばかりなんだから。
        {"text": "You look oddly pleased with yourself.", "audio_url": "assets/reaction_audio/kurisu_belly_8.wav"},  # なんだか妙に満足そうね。
    ],
}



