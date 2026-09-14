/** Add buttons here; motion names match groups in kurisu.model3.json. */
export const interactions = {
  special: 
  {
    backendId: 1,
    motion: "TapReaction",
    label: "Special touch",
    // All four values use the shared 600 x 800 character design space.
    // 15% x 7.5% corresponds to 90 x 60 design pixels.
    position: { top: "45%", left: "50%", width: "30%", height: "10.5%" },
  },

  head: 
  {
    backendId: 2,
    motion: "PatReaction",
    label: "Head Pat",
    // All four values use the shared 600 x 800 character design space.
    // 15% x 7.5% corresponds to 90 x 60 design pixels.
    position: { top: "11%", left: "50%", width: "25%", height: "7.5%" },
  },

  // poke:
  // {
  //   backendId: 3,
  //   motion: "PokeReaction",
  //   label: "Poke",
  // }
};

export type InteractionName = keyof typeof interactions;
