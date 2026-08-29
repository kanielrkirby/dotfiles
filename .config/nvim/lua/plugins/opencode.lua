return {
  {
    "nickjvandyke/opencode.nvim",
    cmd = { "Opencode" },
    keys = {
      { "<leader>Oa", function() require("opencode").ask("@this: ") end, desc = "Ask OpenCode..." },
      { "<leader>Os", function() require("opencode").select() end, desc = "Select OpenCode..." },
      { "<leader>Ogo", function() return require("opencode").operator("@this ") end, desc = "OpenCode operator", expr = true, mode = { "n", "x" } },
      { "<leader>Ogoo", function() return require("opencode").operator("@this ") .. "_" end, desc = "OpenCode line operator", expr = true },
    },
    opts = {},
  },
}
