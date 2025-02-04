export const synth = window.speechSynthesis;
export const mouthState = { value: 0 };
let isSpeaking = false;
let voicesReady = false;

export function initializeSpeech() {
    return new Promise((resolve) => {
        const checkVoices = () => {
            const voices = synth.getVoices();
            if (voices.length > 0) {
                voicesReady = true;
                console.log('Voices loaded:', voices);
                resolve();
            } else {
                setTimeout(checkVoices, 100);
            }
        };

        if (synth.onvoiceschanged !== undefined) {
            synth.onvoiceschanged = checkVoices;
        }

        checkVoices();
    });
}

export function areVoicesReady() {
    return voicesReady;
}

export function speak(text) {
    if (!text || !voicesReady) {
        console.log("Voices not loaded yet.");
        return;
    }

    if (isSpeaking) {
        synth.cancel();
        isSpeaking = false;
        gsap.killTweensOf(mouthState);
        hideSpeechBubble();
    }

    const parts = text.split(/(\{\*\d+\*\})|([.!?]\s+)/).filter(Boolean);
    let partIndex = 0;

    function speakNextPart() {
        if (partIndex < parts.length) {
            const currentPart = parts[partIndex];
            const waitMatch = currentPart.match(/\{\*(\d+)\*\}/);

            if (waitMatch) {
                setTimeout(() => {
                    partIndex++;
                    speakNextPart();
                }, parseInt(waitMatch[1], 10));
            } else {
                const punctuationMatch = currentPart.match(/[.!?]\s*$/);
                const punctuation = punctuationMatch ? punctuationMatch[0] : '';
                const textToSpeak = currentPart.replace(/[.!?]\s*$/, '').trim();
                showSpeechBubble(textToSpeak + punctuation);

                const utterance = new SpeechSynthesisUtterance(textToSpeak);
                const voice = synth.getVoices().find(v => v.name.includes('Female')) || synth.getVoices()[0];

                Object.assign(utterance, {
                    voice: voice,
                    pitch: 1.1,
                    rate: 0.95,
                    onstart: () => {
                        isSpeaking = true;
                        animateMouth();
                    },
                    onend: () => {
                        isSpeaking = false;
                        stopMouthAnimation();
                        hideSpeechBubble();
                        partIndex++;
                        setTimeout(speakNextPart, punctuation ? 500 : 0);
                    }
                });

                synth.speak(utterance);
            }
        }
    }

    speakNextPart();
}

export function animateMouth() {
    gsap.to(mouthState, {
        duration: 0.2,
        value: 1,
        repeat: -1,
        yoyo: true,
        ease: "sine.inOut",
        modifiers: {
            value: () => Math.abs(Math.sin(performance.now() / 200)) * 0.8
        }
    });
}

export function stopMouthAnimation() {
    gsap.killTweensOf(mouthState);
    gsap.to(mouthState, {
        duration: 0.3,
        value: 0,
        ease: "power2.out"
    });
}

function showSpeechBubble(text) {
    const bubble = $('#speech-bubble');
    bubble.text(text).show();

    if (window.currentModel) {
        const bounds = window.currentModel.getBounds();
        const x = window.innerWidth / 2;
        const y = (window.innerHeight / 2) - bounds.height / 2 - 50;

        bubble.css({
            left: `${x - bubble.outerWidth() / 2}px`,
            top: `${y}px`
        });
    }
}

function hideSpeechBubble() {
    $('#speech-bubble').hide();
}

export function isSpeakingNow() {
    return isSpeaking;
}
