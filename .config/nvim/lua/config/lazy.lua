local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not (vim.uv or vim.loop).fs_stat(lazypath) then
  local lazyrepo = "https://github.com/folke/lazy.nvim.git"
  local out = vim.fn.system({ "git", "clone", "--filter=blob:none", "--branch=stable", lazyrepo, lazypath })
  if vim.v.shell_error ~= 0 then
    vim.api.nvim_echo({
      { "Failed to clone lazy.nvim:\n", "ErrorMsg" },
      { out, "WarningMsg" },
      { "\nPress any key to exit..." },
    }, true, {})
    vim.fn.getchar()
    os.exit(1)
  end
end
vim.opt.rtp:prepend(lazypath)

require("lazy").setup({
  spec = {
    -- add LazyVim and import its plugins
    { "LazyVim/LazyVim", import = "lazyvim.plugins" },
    { import = "lazyvim.plugins.extras.ai.copilot" },
    { import = "lazyvim.plugins.extras.coding.mini-surround" },
    { import = "lazyvim.plugins.extras.editor.harpoon2" },
    {
      "ThePrimeagen/harpoon",
      keys = function()
        return {
          { "<leader>a", function() require("harpoon"):list():add() end, desc = "Harpoon add file" },
          {
            "<C-e>",
            function()
              local harpoon = require("harpoon")
              harpoon.ui:toggle_quick_menu(harpoon:list())
            end,
            desc = "Harpoon quick menu",
          },
          { "<C-h>", function() require("harpoon"):list():select(1) end, desc = "Harpoon file 1" },
          { "<C-t>", function() require("harpoon"):list():select(2) end, desc = "Harpoon file 2" },
          { "<C-n>", function() require("harpoon"):list():select(3) end, desc = "Harpoon file 3" },
          { "<C-s>", function() require("harpoon"):list():select(4) end, desc = "Harpoon file 4" },
          { "<C-S-P>", function() require("harpoon"):list():prev() end, desc = "Harpoon prev" },
          { "<C-S-N>", function() require("harpoon"):list():next() end, desc = "Harpoon next" },
        }
      end,
    },
    { import = "lazyvim.plugins.extras.editor.telescope" },
    { import = "lazyvim.plugins.extras.util.gitui" },
    -- import/override with your plugins
    { import = "plugins" },
  },
  defaults = {
    -- By default, only LazyVim plugins will be lazy-loaded. Your custom plugins will load during startup.
    -- If you know what you're doing, you can set this to `true` to have all your custom plugins lazy-loaded by default.
    lazy = false,
    -- It's recommended to leave version=false for now, since a lot the plugin that support versioning,
    -- have outdated releases, which may break your Neovim install.
    version = false,
  },
  checker = {
    -- check for plugin updates periodically
    enabled = true,
    -- notify on update
    notify = false,
  },
  install = { colorscheme = { "tokyonight", "habamax" } },
  performance = {
    rtp = {
      -- disable some rtp plugins
      disabled_plugins = {
        "gzip",
        -- "matchit",
        -- "matchparen",
        -- "netrwPlugin",
        "tarPlugin",
        "tohtml",
        "tutor",
        "zipPlugin",
      },
    },
  },
})
