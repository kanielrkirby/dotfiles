return {
  {
    "tpope/vim-fugitive",
    cmd = { "Git", "G", "Gdiffsplit", "Gread", "Gwrite" },
    keys = {
      { "<leader>gg", "<cmd>Git<cr>", desc = "Git status" },
    },
  },
}
