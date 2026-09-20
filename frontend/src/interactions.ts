/** Add buttons here; motion names match groups in kurisu.model3.json. */
export const interactions = {
  special: 
  {
    backendId: 1,
    motion: "TapReaction",
    label: "Special touch",
    // All four values use the shared 600 x 800 character design space.
    // 15% x 7.5% corresponds to 90 x 60 design pixels.
    position: { top: "47.5%", left: "50.5%", width: "20%", height: "10.5%" },
  },

  head: 
  {
    backendId: 2,
    motion: "PatReaction",
    label: "Head Pat",
    // All four values use the shared 600 x 800 character design space.
    // 15% x 7.5% corresponds to 90 x 60 design pixels.
    position: { top: "10.5%", left: "50%", width: "25%", height: "10.5%" },
  },

  poke_neck: // I'm gonna change this to tickle_neck later. but now is poke, very gentle!
  {
    backendId: 3,
    motion: "PokeReaction",
    label: "Poke_neck",
    position: { top: "30%", left: "50%", width: "10%", height: "4.5%" },
  },

  poke_arm_left:
  {
    backendId: 4,
    motion: "PokeReaction",
    label: "Poke_arm_left",
    position: { top: "58%", left: "32%", width: "5%", height: "40%" },
  },

  poke_arm_right:
  {
    backendId: 4,
    motion: "PokeReaction",
    label: "Poke_arm_right",
    position: { top: "58%", left: "67%", width: "5%", height: "40%" },
  },

  belly_rub:
  {
    backendId: 5,
    motion: "PokeReaction",
    label: "belly_rub",
    position: { top: "65%", left: "50%", width: "25%", height: "15%" },
  }

};

export type InteractionName = keyof typeof interactions;
