class RemoteAssistDisplay {
  constructor() {
    this.initAttempts = 0;
    this.initializeWhenReady();
  }

  async initializeWhenReady(attempts = 0) {
    if (attempts > 50) {
      console.log("Failed to initialize after 50 attempts");
      return;
    }

    try {
      const ha = document.querySelector("home-assistant");
      if (!ha?.shadowRoot || !ha.hass) {
        throw new Error("Home Assistant not ready");
      }

      const main = ha.shadowRoot.querySelector("home-assistant-main");
      if (!main?.shadowRoot) {
        throw new Error("Main UI not ready");
      }

      this.ha = ha;
      this.main = main.shadowRoot;
      this.initAttempts = 0;

      console.log("RemoteAssistDisplay initialized");

      await this.run();

      // Set up observers
      this.setupObservers();

    } catch (e) {
      setTimeout(() => this.initializeWhenReady(attempts + 1), 100);
    }
  }

  setupObservers() {
    const resolver = this.main.querySelector("partial-panel-resolver");
    if (resolver) {
      console.log("Setting up observers");
      new MutationObserver(() => {
        clearTimeout(this.updateTimer);
        this.updateTimer = setTimeout(() => this.run(), 100);
      }).observe(resolver, { childList: true });
    }

    window.addEventListener("location-changed", () => {
      clearTimeout(this.updateTimer);
      this.updateTimer = setTimeout(() => this.run(), 100);
    });
  }

  async run() {
    const lovelace = this.main.querySelector("ha-panel-lovelace");
    if (!lovelace) {
      console.log("No lovelace panel found");
      return;
    }

    const displayId = localStorage.getItem("remote_assist_display_id");
    if (!displayId) return;

    const settings = JSON.parse(localStorage.getItem(`remote_assist_display_settings`) || "{}");
    if (!settings.hideHeader && !settings.hideSidebar) return;

    console.log("Checking Lovelace configuration");

    this.initAttempts++;
    try {
      await this.waitForElement(() => lovelace.lovelace?.config, "Lovelace config");
      const huiRoot = lovelace.shadowRoot?.querySelector("hui-root");
      await this.waitForElement(() => huiRoot?.shadowRoot, "hui-root shadow");

      console.log("Processing settings:", settings);
      await this.processConfig(huiRoot, settings);
    } catch (e) {
      console.log("Configuration error:", e);
    }
  }

  async waitForElement(getter, name, maxAttempts = 100) {
    for (let i = 0; i < maxAttempts; i++) {
      const result = getter();
      if (result) return result;
      await new Promise(r => setTimeout(r, 50));
    }
    throw new Error(`Timeout waiting for ${name}`);
  }

  async processConfig(huiRoot, settings) {
    if (!huiRoot.shadowRoot) return;

    if (settings.hideHeader) {
      console.log("Applying header modifications");
      const view = huiRoot.shadowRoot.querySelector("#view");
      if (view) {
        view.style.setProperty("min-height", "100vh", "important");
        view.style.setProperty("padding-top", "calc(0px + env(safe-area-inset-top))", "important");
      }

      const header = huiRoot.shadowRoot.querySelector("header");
      if (header) {
        header.style.setProperty("display", "none", "important");
      }

      huiRoot.style.setProperty("--header-height", "0", "important");
      document.documentElement.style.setProperty("--header-height", "0", "important");
    }

    if (settings.hideSidebar) {
      console.log("Applying sidebar modifications");

      // Set the drawer width to 0
      this.main.host.style.setProperty("--mdc-drawer-width", "0", "important");

      // Make sure panel takes full width
      const panel = this.main.querySelector("partial-panel-resolver");
      if (panel) {
        panel.style.setProperty("--mdc-top-app-bar-width", "100%", "important");
      }

      // Hide the sidebar itself
      const sidebar = this.main.querySelector("ha-drawer ha-sidebar");
      if (sidebar) {
        sidebar.style.setProperty("display", "none", "important");
      }

      // Hide the menu button
      const menuButton = huiRoot.shadowRoot.querySelector("ha-menu-button");
      if (menuButton) {
        menuButton.style.setProperty("display", "none", "important");
      }
    }

    window.dispatchEvent(new Event("resize"));
  }
}

// Wait for core web components
Promise.all([
  customElements.whenDefined("home-assistant"),
  customElements.whenDefined("hui-view")
]).then(() => {
  console.log("Starting RemoteAssistDisplay");
  window.RemoteAssistDisplay = new RemoteAssistDisplay();
});