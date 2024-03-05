module.exports = function (json) {
  return {
    osStr: {
      type: String,
    },
    version: {
      type: String,
      default: (t) => t.get("build"),
    },
    safariVersion: {
      type: String,
    },
    build: {
      type: String,
      default: (t) => t.get("version"),
    },
    key: {
      type: String,
      default: (t) => json.osStr + ";" + t.get("key"),
    },
    embeddedOSBuild: {
      type: String,
    },
    bridgeOSBuild: {
      type: String,
    },
    buildTrain: {
      type: String,
    },
    released: {
      type: String,
      default: () => "1970-01-01",
    },
    rc: {
      type: Boolean,
    },
    beta: {
      type: Boolean,
    },
    rsr: {
      type: Boolean,
    },
    internal: {
      type: Boolean,
    },
    hideFromLatestVersions: {
      type: Boolean,
    },
    preinstalled: {
      type: Array,
      method(t) {
        if (json.preinstalled === true) return t.get("deviceMap");
        if (Array.isArray(json.preinstalled)) return json.preinstalled;
        return [];
      },
    },
    //"createDuplicateEntries",
    notes: {
      type: String,
    },
    releaseNotes: {
      type: String,
    },
    securityNotes: {
      type: String,
    },
    ipd: {
      type: Object,
    },
    appledbWebImage: {
      type: Object,
      default: () => {
        return {
          id: "",
          align: "left",
        };
      },
    },
    appledbUrl: {
      type: String,
      default: (t) =>
        encodeURI(
          `https://appledb.dev/firmware/${json.osStr.replace(/ /g, "-")}/${t.get("key")}.html`,
        ),
    },
    deviceMap: {
      type: Array,
    },
    osMap: {
      type: Array,
    },
    sdks: {
      type: Array,
    },
    sources: {
      type: Array,
    },
  };
};
