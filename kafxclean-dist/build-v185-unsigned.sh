#!/bin/sh
set -eu

rm -rf /work /out
mkdir -p /work/app/src/main/java/com/example/CleanTwitter /work/app/src/main/assets /work/app/src/main/res/layout /work/app/src/main/res/values /work/app/src/main/res/drawable /work/app/src/test/java/com/example/CleanTwitter /work/tests /out

cat > /work/settings.gradle.kts <<'__SETTINGS__'
pluginManagement {
    repositories { google(); mavenCentral(); gradlePluginPortal() }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories { google(); mavenCentral() }
}
rootProject.name = "KafXClean"
include(":app")
__SETTINGS__

cat > /work/build.gradle.kts <<'__ROOT__'
plugins {
    id("com.android.application") version "9.4.0" apply false
}
__ROOT__

cat > /work/gradle.properties <<'__PROPS__'
org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8
org.gradle.workers.max=1
org.gradle.parallel=false
org.gradle.daemon=false
android.useAndroidX=true
android.nonTransitiveRClass=true
__PROPS__

cat > /work/app/build.gradle.kts <<'__APP__'
plugins {
    id("com.android.application")
}
android {
    namespace = "com.example.CleanTwitter"
    compileSdk = 36
    defaultConfig {
        applicationId = "com.example.CleanTwitter"
        minSdk = 24
        targetSdk = 36
        versionCode = 14
        versionName = "1.8.5"
    }
    buildTypes {
        release {
            isMinifyEnabled = false
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}
dependencies {
    implementation("androidx.activity:activity:1.13.0")
    testImplementation("junit:junit:4.13.2")
}
__APP__

mkdir -p "/work/$(dirname 'app/src/main/java/com/example/CleanTwitter/MainActivity.kt')"
cat > "/work/app/src/main/java/com/example/CleanTwitter/MainActivity.kt" <<'__KAFX_V185_0__'
package com.example.CleanTwitter

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.view.View
import android.webkit.CookieManager
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.ProgressBar
import androidx.activity.ComponentActivity
import androidx.activity.OnBackPressedCallback
import androidx.activity.result.ActivityResultLauncher
import androidx.activity.result.contract.ActivityResultContracts
import androidx.core.view.ViewCompat
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import java.io.ByteArrayInputStream
import java.util.regex.Pattern

class MainActivity : ComponentActivity() {
    private lateinit var webView: WebView
    private lateinit var progressBar: ProgressBar
    private lateinit var fileChooserLauncher: ActivityResultLauncher<Intent>
    private lateinit var backCallback: OnBackPressedCallback
    private lateinit var filterScript: String
    private var fileUploadCallback: android.webkit.ValueCallback<Array<Uri>>? = null

    companion object {
        private const val X_HOME = "https://x.com/home"
        private val AD_URL_PATTERNS = arrayOf(
            Pattern.compile("^https?://([^/]+\\.)?ads\\.twitter\\.com/.*", Pattern.CASE_INSENSITIVE),
            Pattern.compile("^https?://([^/]+\\.)?analytics\\.twitter\\.com/.*", Pattern.CASE_INSENSITIVE),
            Pattern.compile("^https?://([^/]+\\.)?doubleclick\\.net/.*", Pattern.CASE_INSENSITIVE),
            Pattern.compile("^https?://([^/]+\\.)?googlesyndication\\.com/.*", Pattern.CASE_INSENSITIVE),
            Pattern.compile("^https?://([^/]+\\.)?google-analytics\\.com/.*", Pattern.CASE_INSENSITIVE),
            Pattern.compile("^https?://([^/]+\\.)?googletagmanager\\.com/.*", Pattern.CASE_INSENSITIVE)
        )

        internal fun isAdUrl(url: String): Boolean = AD_URL_PATTERNS.any { it.matcher(url).matches() }

        internal fun isXHost(host: String?): Boolean {
            val value = host?.lowercase() ?: return false
            return value == "x.com" || value.endsWith(".x.com") || value == "twitter.com" || value.endsWith(".twitter.com")
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        WindowCompat.setDecorFitsSystemWindows(window, false)
        setContentView(R.layout.activity_main)

        webView = findViewById(R.id.webview)
        progressBar = findViewById(R.id.progressBar)
        filterScript = assets.open("filter.js").bufferedReader().use { it.readText() }

        ViewCompat.setOnApplyWindowInsetsListener(findViewById(android.R.id.content)) { view, insets ->
            val bars = insets.getInsets(WindowInsetsCompat.Type.systemBars() or WindowInsetsCompat.Type.displayCutout())
            view.setPadding(bars.left, bars.top, bars.right, bars.bottom)
            insets
        }

        fileChooserLauncher = registerForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
            fileUploadCallback?.onReceiveValue(WebChromeClient.FileChooserParams.parseResult(result.resultCode, result.data))
            fileUploadCallback = null
        }

        backCallback = object : OnBackPressedCallback(false) {
            override fun handleOnBackPressed() {
                webView.evaluateJavascript("window.KAFX?.prepareBack?.()") {
                    webView.goBack()
                }
            }
        }
        onBackPressedDispatcher.addCallback(this, backCallback)

        initializeWebView()
        webView.loadUrl(X_HOME)
    }

    private fun initializeWebView() {
        CookieManager.getInstance().setAcceptCookie(true)
        webView.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            allowFileAccess = false
            mixedContentMode = WebSettings.MIXED_CONTENT_NEVER_ALLOW
        }
        webView.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView?, request: WebResourceRequest?): Boolean {
                val uri = request?.url ?: return false
                if (isXHost(uri.host)) return false
                startActivity(Intent(Intent.ACTION_VIEW, uri))
                return true
            }

            override fun shouldInterceptRequest(view: WebView?, request: WebResourceRequest?): WebResourceResponse? {
                val url = request?.url?.toString() ?: return null
                if (!isAdUrl(url)) return null
                return WebResourceResponse("text/plain", "UTF-8", ByteArrayInputStream(ByteArray(0)))
            }

            override fun onPageFinished(view: WebView?, url: String?) {
                injectFilter()
                updateBackState()
            }

            override fun doUpdateVisitedHistory(view: WebView?, url: String?, isReload: Boolean) {
                updateBackState()
            }
        }
        webView.webChromeClient = object : WebChromeClient() {
            override fun onProgressChanged(view: WebView?, newProgress: Int) {
                progressBar.progress = newProgress
                progressBar.visibility = if (newProgress < 100) View.VISIBLE else View.GONE
            }

            override fun onShowFileChooser(
                webView: WebView?,
                filePathCallback: android.webkit.ValueCallback<Array<Uri>>?,
                fileChooserParams: FileChooserParams?
            ): Boolean {
                fileUploadCallback?.onReceiveValue(null)
                fileUploadCallback = filePathCallback
                fileChooserLauncher.launch(fileChooserParams?.createIntent() ?: Intent(Intent.ACTION_OPEN_DOCUMENT).apply {
                    type = "*/*"
                    addCategory(Intent.CATEGORY_OPENABLE)
                })
                return true
            }
        }
    }

    private fun injectFilter() {
        webView.evaluateJavascript(filterScript, null)
    }

    private fun updateBackState() {
        backCallback.isEnabled = webView.canGoBack()
    }

    override fun onDestroy() {
        fileUploadCallback?.onReceiveValue(null)
        webView.destroy()
        super.onDestroy()
    }
}

__KAFX_V185_0__

mkdir -p "/work/$(dirname 'app/src/main/assets/filter.js')"
cat > "/work/app/src/main/assets/filter.js" <<'__KAFX_V185_1__'
(() => {
  "use strict";

  if (window.KAFX) {
    window.KAFX.scan();
    return;
  }

  const CELL = '[data-testid="cellInnerDiv"]';
  const VIDEO = `${CELL} article video, ${CELL} article [data-testid="videoPlayer"], ${CELL} article [data-testid="videoComponent"], ${CELL} article [data-testid="playButton"]`;
  const AD_MARKER = `${CELL} [data-testid*="placementTracking"], ${CELL} [data-testid*="placementtracking"], ${CELL} [data-testid*="promoted"]`;
  const REPOST_CONTEXT = `${CELL} article [data-testid="socialContext"]`;
  const STATUS_LINK = `${CELL} article a[href*="/status/"]`;
  const AD_LABELS = new Set(["promoted", "プロモーション"]);
  const FOLLOWING_LABELS = new Set(["following", "フォロー中"]);
  const FOR_YOU_LABELS = new Set(["for you", "おすすめ"]);
  const PURCHASE_LABELS = new Set(["購入する", "get premium", "upgrade to premium"]);
  const RESTORE_KEY = "kafx.restore.next";
  const ANCHOR_PREFIX = "kafx.anchor.";
  const RESTORE_TTL_MS = 15000;
  const RESTORE_MAX_ATTEMPTS = 20;
  let timer = 0;
  let captureTimer = 0;
  let restoreAttempts = 0;
  let restorePending = false;

  const normalize = value => (value || "").trim().toLowerCase();
  const cellOf = element => element.closest(CELL);
  const timelineTabs = () => Array.from(document.querySelectorAll('[role="tablist"] [role="tab"]'));
  const pageKey = () => `${location.origin}${location.pathname}${location.search}`;
  const anchorKey = () => `${ANCHOR_PREFIX}${pageKey()}`;
  const statusId = href => (href || "").match(/\/status\/(\d+)/)?.[1] || "";
  const isRepost = text => {
    const value = normalize(text);
    return value.includes("リポストしました") || /\breposted\b/.test(value);
  };

  const readRestoreFlag = () => {
    const raw = sessionStorage.getItem(RESTORE_KEY);
    if (!raw) return false;
    if (Date.now() - Number(raw) <= RESTORE_TTL_MS) return true;
    sessionStorage.removeItem(RESTORE_KEY);
    return false;
  };

  restorePending = readRestoreFlag();

  const finishRestore = () => {
    sessionStorage.removeItem(RESTORE_KEY);
    restorePending = false;
    restoreAttempts = 0;
  };

  const ensureFollowing = tabs => {
    const tab = tabs.find(item => FOLLOWING_LABELS.has(normalize(item.textContent)));
    if (!tab || tab.getAttribute("aria-selected") === "true") return false;
    tab.click();
    return true;
  };

  const hideForYouTab = tabs => {
    tabs.forEach(tab => {
      if (!FOR_YOU_LABELS.has(normalize(tab.textContent))) return;
      const tablist = tab.closest('[role="tablist"]');
      const presentation = tab.closest('[role="presentation"]');
      const target = presentation && presentation.closest('[role="tablist"]') === tablist ? presentation : tab;
      target.style.setProperty("display", "none", "important");
    });
  };

  const hidePurchaseButtons = () => {
    document.querySelectorAll('button, [role="button"], a[role="link"]').forEach(element => {
      if (PURCHASE_LABELS.has(normalize(element.textContent))) {
        element.style.setProperty("display", "none", "important");
      }
    });
  };

  const captureAnchor = () => {
    if (restorePending) return;
    const viewportHeight = window.innerHeight || 0;
    let best = null;

    document.querySelectorAll(STATUS_LINK).forEach(link => {
      const cell = cellOf(link);
      const id = statusId(link.getAttribute("href"));
      if (!cell || !id || cell.style.display === "none") return;
      const rect = cell.getBoundingClientRect();
      if (rect.bottom <= 0 || (viewportHeight && rect.top >= viewportHeight)) return;
      const score = Math.abs(rect.top);
      if (!best || score < best.score) best = { id, offset: rect.top, score };
    });

    if (best) {
      sessionStorage.setItem(anchorKey(), JSON.stringify({ id: best.id, offset: best.offset }));
    }
  };

  const restoreAnchor = () => {
    const raw = sessionStorage.getItem(anchorKey());
    if (!raw) {
      finishRestore();
      return false;
    }

    const anchor = JSON.parse(raw);
    const link = document.querySelector(`${CELL} article a[href*="/status/${anchor.id}"]`);
    const cell = link && cellOf(link);
    if (!cell || cell.style.display === "none") return false;

    const delta = cell.getBoundingClientRect().top - Number(anchor.offset || 0);
    finishRestore();
    if (Math.abs(delta) > 1) window.scrollBy(0, delta);
    return true;
  };

  const scan = () => {
    timer = 0;
    if (restorePending && !readRestoreFlag()) restorePending = false;

    let tabs = timelineTabs();
    if (!restorePending && ensureFollowing(tabs)) tabs = timelineTabs();
    hideForYouTab(tabs);
    hidePurchaseButtons();

    const tweetCells = new Set();
    const videoCells = new Set();
    const adCells = new Set();
    const repostCells = new Set();

    document.querySelectorAll(`${CELL} article`).forEach(element => {
      const cell = cellOf(element);
      if (cell) tweetCells.add(cell);
    });

    document.querySelectorAll(VIDEO).forEach(element => {
      const cell = cellOf(element);
      if (cell) videoCells.add(cell);
    });

    document.querySelectorAll(AD_MARKER).forEach(element => {
      const cell = cellOf(element);
      if (cell) adCells.add(cell);
    });

    document.querySelectorAll(`${CELL} span`).forEach(element => {
      if (!AD_LABELS.has(normalize(element.textContent))) return;
      const cell = cellOf(element);
      if (cell) adCells.add(cell);
    });

    document.querySelectorAll(REPOST_CONTEXT).forEach(element => {
      if (!isRepost(element.textContent)) return;
      const cell = cellOf(element);
      if (cell) repostCells.add(cell);
    });

    tweetCells.forEach(cell => {
      const hidden = adCells.has(cell) || videoCells.has(cell) || repostCells.has(cell);
      cell.style.setProperty("display", hidden ? "none" : "", hidden ? "important" : "");
    });

    if (restorePending) {
      restoreAttempts += 1;
      restoreAnchor();
      if (restorePending && restoreAttempts < RESTORE_MAX_ATTEMPTS) {
        timer = window.setTimeout(scan, 120);
      } else if (restorePending) {
        finishRestore();
      }
    }

    if (!restorePending) captureAnchor();
  };

  const schedule = () => {
    if (timer) return;
    timer = window.setTimeout(scan, 120);
  };

  const scheduleCapture = () => {
    if (restorePending || captureTimer) return;
    captureTimer = window.setTimeout(() => {
      captureTimer = 0;
      captureAnchor();
    }, 80);
  };

  const prepareBack = () => {
    captureAnchor();
    sessionStorage.setItem(RESTORE_KEY, String(Date.now()));
  };

  const prepareRestore = () => {
    restorePending = readRestoreFlag();
    restoreAttempts = 0;
    if (restorePending) schedule();
  };

  const start = () => {
    new MutationObserver(schedule).observe(document.body, { childList: true, subtree: true });
    document.addEventListener("click", captureAnchor, true);
    window.addEventListener("scroll", scheduleCapture, { passive: true });
    window.addEventListener("popstate", prepareRestore, { passive: true });
    window.addEventListener("pageshow", prepareRestore, { passive: true });
    scan();
  };

  window.KAFX = { scan, captureAnchor, prepareBack };
  if (document.body) start();
  else document.addEventListener("DOMContentLoaded", start, { once: true });
})();

__KAFX_V185_1__

mkdir -p "/work/$(dirname 'app/src/main/AndroidManifest.xml')"
cat > "/work/app/src/main/AndroidManifest.xml" <<'__KAFX_V185_2__'
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-permission android:name="android.permission.INTERNET" />

    <application
        android:allowBackup="false"
        android:icon="@drawable/ic_launcher_brand"
        android:label="@string/app_name"
        android:roundIcon="@drawable/ic_launcher_brand"
        android:supportsRtl="true"
        android:theme="@style/Theme.AdLessTwitter">
        <activity
            android:name=".MainActivity"
            android:configChanges="orientation|screenSize|screenLayout|smallestScreenSize"
            android:exported="true"
            android:windowSoftInputMode="adjustResize">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>

__KAFX_V185_2__

mkdir -p "/work/$(dirname 'app/src/main/res/layout/activity_main.xml')"
cat > "/work/app/src/main/res/layout/activity_main.xml" <<'__KAFX_V185_3__'
<?xml version="1.0" encoding="utf-8"?>
<FrameLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:background="@android:color/black">

    <WebView
        android:id="@+id/webview"
        android:layout_width="match_parent"
        android:layout_height="match_parent" />

    <ProgressBar
        android:id="@+id/progressBar"
        style="?android:attr/progressBarStyleHorizontal"
        android:layout_width="match_parent"
        android:layout_height="4dp"
        android:layout_gravity="top"
        android:max="100"
        android:visibility="gone" />
</FrameLayout>

__KAFX_V185_3__

mkdir -p "/work/$(dirname 'app/src/main/res/values/strings.xml')"
cat > "/work/app/src/main/res/values/strings.xml" <<'__KAFX_V185_4__'
<resources>
    <string name="app_name">KafXClean</string>
</resources>

__KAFX_V185_4__

mkdir -p "/work/$(dirname 'app/src/main/res/values/themes.xml')"
cat > "/work/app/src/main/res/values/themes.xml" <<'__KAFX_V185_5__'
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="Theme.AdLessTwitter" parent="@android:style/Theme.Material.NoActionBar">
        <item name="android:statusBarColor">#000000</item>
        <item name="android:windowBackground">#000000</item>
    </style>
</resources>

__KAFX_V185_5__

mkdir -p "/work/$(dirname 'app/src/main/res/drawable/ic_launcher_brand.xml')"
cat > "/work/app/src/main/res/drawable/ic_launcher_brand.xml" <<'__KAFX_V185_6__'
<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="108"
    android:viewportHeight="108">

    <path
        android:fillColor="#A78BFA"
        android:pathData="M18,0H90C100,0 108,8 108,18V90C108,100 100,108 90,108H18C8,108 0,100 0,90V18C0,8 8,0 18,0Z" />

    <path
        android:fillColor="#FFFFFF"
        android:pathData="M47,44L54,27C56,21 63,21 66,27L89,79C92,85 89,92 83,92C79,92 76,90 74,86L61,62C59,58 56,56 51,56H42Z" />

    <path
        android:fillColor="#FFFFFF"
        android:pathData="M45,67H52C57,67 61,69 64,74L72,88H59C55,80 50,78 43,78H38Z" />

    <path
        android:fillColor="#FFFFFF"
        android:pathData="M18,48H40C42.2,48 44,49.8 44,52C44,54.2 42.2,56 40,56H18C15.8,56 14,54.2 14,52C14,49.8 15.8,48 18,48Z" />

    <path
        android:fillColor="#FFFFFF"
        android:pathData="M12,60H38C40.2,60 42,61.8 42,64C42,66.2 40.2,68 38,68H12C9.8,68 8,66.2 8,64C8,61.8 9.8,60 12,60Z" />

    <path
        android:fillColor="#EDE8FF"
        android:pathData="M20,72H34C36.2,72 38,73.8 38,76C38,78.2 36.2,80 34,80H20C17.8,80 16,78.2 16,76C16,73.8 17.8,72 20,72Z" />
</vector>

__KAFX_V185_6__

mkdir -p "/work/$(dirname 'app/src/test/java/com/example/CleanTwitter/AdBlockTest.kt')"
cat > "/work/app/src/test/java/com/example/CleanTwitter/AdBlockTest.kt" <<'__KAFX_V185_7__'
package com.example.CleanTwitter

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class AdBlockTest {
    @Test
    fun blocksKnownAdAndTrackingHosts() {
        listOf(
            "https://ads.twitter.com/123",
            "https://analytics.twitter.com/track",
            "https://googleads.g.doubleclick.net/pagead",
            "https://pagead2.googlesyndication.com/pagead.js",
            "https://www.google-analytics.com/g/collect",
            "https://www.googletagmanager.com/gtm.js"
        ).forEach { assertTrue(it, MainActivity.isAdUrl(it)) }
    }

    @Test
    fun keepsXContentHosts() {
        listOf(
            "https://x.com/home",
            "https://api.x.com/1.1/test",
            "https://twitter.com/notifications",
            "https://api.twitter.com/graphql"
        ).forEach { assertFalse(it, MainActivity.isAdUrl(it)) }
    }

    @Test
    fun recognizesXHosts() {
        assertTrue(MainActivity.isXHost("x.com"))
        assertTrue(MainActivity.isXHost("mobile.x.com"))
        assertTrue(MainActivity.isXHost("twitter.com"))
        assertTrue(MainActivity.isXHost("mobile.twitter.com"))
        assertFalse(MainActivity.isXHost("example.com"))
        assertFalse(MainActivity.isXHost("notx.com"))
    }
}

__KAFX_V185_7__

mkdir -p "/work/$(dirname 'tests/filter-dom.test.mjs')"
cat > "/work/tests/filter-dom.test.mjs" <<'__KAFX_V185_8__'
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import vm from "node:vm";

const FILTER_PATH = "app/src/main/assets/filter.js";
const FILTER_SOURCE = readFileSync(FILTER_PATH, "utf8");
const CELL = '[data-testid="cellInnerDiv"]';
const TABS = '[role="tablist"] [role="tab"]';
const BUTTONS = 'button, [role="button"], a[role="link"]';
const ARTICLES = `${CELL} article`;
const VIDEO = `${CELL} article video, ${CELL} article [data-testid="videoPlayer"], ${CELL} article [data-testid="videoComponent"], ${CELL} article [data-testid="playButton"]`;
const AD_MARKER = `${CELL} [data-testid*="placementTracking"], ${CELL} [data-testid*="placementtracking"], ${CELL} [data-testid*="promoted"]`;
const SPANS = `${CELL} span`;
const REPOST_CONTEXT = `${CELL} article [data-testid="socialContext"]`;
const STATUS_LINK = `${CELL} article a[href*="/status/"]`;
const RESTORE_KEY = "kafx.restore.next";

class FakeStyle {
  constructor() { this.values = new Map(); }
  setProperty(name, value, priority = "") { this.values.set(name, { value, priority }); }
  get display() { return this.values.get("display")?.value; }
}
class FakeElement {
  constructor({ text = "", attributes = {}, top = 0, height = 100 } = {}) {
    this.textContent = text;
    this.attributes = new Map(Object.entries(attributes));
    this.ancestors = new Map();
    this.style = new FakeStyle();
    this.clickCount = 0;
    this.top = top;
    this.height = height;
  }
  getAttribute(name) { return this.attributes.get(name) ?? null; }
  setAttribute(name, value) { this.attributes.set(name, value); }
  click() { this.clickCount += 1; this.attributes.set("aria-selected", "true"); }
  closest(selector) { return this.ancestors.get(selector) ?? null; }
  getBoundingClientRect() { return { top: this.top, bottom: this.top + this.height }; }
}
function underCell(cell, options) {
  const element = new FakeElement(options);
  element.ancestors.set(CELL, cell);
  return element;
}
function makeFixture({ following = "Following", forYou = "For you", premium = "Get Premium", rerenderTabs = false } = {}) {
  const tablist = new FakeElement();
  const presentation = new FakeElement();
  presentation.ancestors.set('[role="tablist"]', tablist);
  const followingTab = new FakeElement({ text: following, attributes: { "aria-selected": "false" } });
  followingTab.ancestors.set('[role="tablist"]', tablist);
  const forYouTab = new FakeElement({ text: forYou });
  forYouTab.ancestors.set('[role="tablist"]', tablist);
  forYouTab.ancestors.set('[role="presentation"]', presentation);
  const purchase = new FakeElement({ text: premium });

  const normalCell = new FakeElement({ top: 64 });
  const videoCell = new FakeElement({ top: 180 });
  const markerAdCell = new FakeElement({ top: 300 });
  const labelAdCell = new FakeElement({ top: 420 });
  const repostCell = new FakeElement({ top: 540 });
  const englishRepostCell = new FakeElement({ top: 660 });
  const quoteCell = new FakeElement({ top: 720 });
  const normalLink = underCell(normalCell, { attributes: { href: "/alice/status/111" } });

  const selectors = new Map([
    [TABS, [followingTab, forYouTab]],
    [BUTTONS, [purchase]],
    [ARTICLES, [normalCell, videoCell, markerAdCell, labelAdCell, repostCell, englishRepostCell, quoteCell].map(cell => underCell(cell))],
    [VIDEO, [underCell(videoCell)]],
    [AD_MARKER, [underCell(markerAdCell)]],
    [SPANS, [underCell(labelAdCell, { text: "Promoted" }), underCell(quoteCell, { text: "I wrote about repost behavior" })]],
    [REPOST_CONTEXT, [underCell(repostCell, { text: "Bobさんがリポストしました" }), underCell(englishRepostCell, { text: "Bob reposted" })]],
    [STATUS_LINK, [normalLink]],
  ]);

  let rerenderPresentation = null;
  if (rerenderTabs) {
    const originalClick = followingTab.click.bind(followingTab);
    followingTab.click = () => {
      originalClick();
      const nextTablist = new FakeElement();
      const nextFollowing = new FakeElement({ text: following, attributes: { "aria-selected": "true" } });
      nextFollowing.ancestors.set('[role="tablist"]', nextTablist);
      const nextForYou = new FakeElement({ text: forYou });
      rerenderPresentation = new FakeElement();
      rerenderPresentation.ancestors.set('[role="tablist"]', nextTablist);
      nextForYou.ancestors.set('[role="tablist"]', nextTablist);
      nextForYou.ancestors.set('[role="presentation"]', rerenderPresentation);
      selectors.set(TABS, [nextFollowing, nextForYou]);
    };
  }

  const documentListeners = new Map();
  const windowListeners = new Map();
  const storage = new Map();
  const sessionStorage = {
    getItem: key => storage.get(key) ?? null,
    setItem: (key, value) => storage.set(key, String(value)),
    removeItem: key => storage.delete(key),
  };
  const location = { origin: "https://x.com", pathname: "/home", search: "", href: "https://x.com/home" };
  const setLocation = pathname => {
    location.pathname = pathname;
    location.search = "";
    location.href = `${location.origin}${pathname}`;
  };
  const querySelector = selector => {
    const id = selector.match(/\/status\/(\d+)/)?.[1];
    if (id) return (selectors.get(STATUS_LINK) ?? []).find(link => link.getAttribute("href")?.includes(`/status/${id}`)) ?? null;
    return (selectors.get(selector) ?? [])[0] ?? null;
  };
  const document = {
    body: {},
    querySelectorAll: selector => selectors.get(selector) ?? [],
    querySelector,
    addEventListener: (name, callback) => documentListeners.set(name, callback),
  };
  const timers = [];
  const scrolls = [];
  let observerCallback = null;
  let observerCount = 0;
  const window = {
    innerHeight: 800,
    setTimeout(callback) { timers.push(callback); return timers.length; },
    scrollBy(x, y) { scrolls.push({ x, y }); },
    addEventListener(name, callback) { windowListeners.set(name, callback); },
  };
  const context = {
    document,
    window,
    location,
    sessionStorage,
    MutationObserver: class {
      constructor(callback) { observerCallback = callback; observerCount += 1; }
      observe() {}
    },
  };
  vm.runInNewContext(FILTER_SOURCE, context, { filename: FILTER_PATH });

  const flushTimers = () => {
    while (timers.length) timers.shift()();
  };

  return {
    context, selectors, timers, storage, scrolls, setLocation, flushTimers,
    mutate: () => observerCallback(), observerCount: () => observerCount,
    popstate: () => windowListeners.get("popstate")?.(),
    followingTab, forYouPresentation: presentation, purchase,
    normalCell, videoCell, markerAdCell, labelAdCell, repostCell, englishRepostCell, quoteCell,
    get rerenderPresentation() { return rerenderPresentation; },
  };
}

test("canonical filter enforces the timeline contract", () => {
  const f = makeFixture();
  assert.equal(f.followingTab.clickCount, 1);
  assert.equal(f.forYouPresentation.style.display, "none");
  assert.equal(f.purchase.style.display, "none");
  assert.equal(f.normalCell.style.display, "");
  assert.equal(f.videoCell.style.display, "none");
  assert.equal(f.markerAdCell.style.display, "none");
  assert.equal(f.labelAdCell.style.display, "none");
});

test("reposts are hidden without matching ordinary tweet text", () => {
  const f = makeFixture();
  assert.equal(f.repostCell.style.display, "none");
  assert.equal(f.englishRepostCell.style.display, "none");
  assert.equal(f.quoteCell.style.display, "");
});

test("Japanese labels use the same production path", () => {
  const f = makeFixture({ following: "フォロー中", forYou: "おすすめ", premium: "購入する" });
  assert.equal(f.followingTab.clickCount, 1);
  assert.equal(f.forYouPresentation.style.display, "none");
  assert.equal(f.purchase.style.display, "none");
});

test("For You is hidden after Following rerenders the tablist", () => {
  const f = makeFixture({ rerenderTabs: true });
  assert.equal(f.followingTab.clickCount, 1);
  assert.equal(f.rerenderPresentation.style.display, "none");
});

test("back restore keeps the same tweet viewport offset after filtering", () => {
  const f = makeFixture();
  assert.equal(f.normalCell.top, 64);
  f.setLocation("/alice/status/999");
  f.context.window.KAFX.prepareBack();
  f.setLocation("/home");
  f.followingTab.setAttribute("aria-selected", "false");
  f.normalCell.top = 300;
  f.popstate();
  f.flushTimers();
  assert.deepEqual(f.scrolls.at(-1), { x: 0, y: 236 });
  assert.equal(f.followingTab.clickCount, 1);
  assert.equal(f.storage.has(RESTORE_KEY), false);
});

test("mutation rescan and reinjection stay deterministic", () => {
  const f = makeFixture();
  const late = new FakeElement();
  f.selectors.get(ARTICLES).push(underCell(late));
  f.selectors.get(VIDEO).push(underCell(late));
  f.mutate();
  f.mutate();
  assert.equal(f.timers.length, 1);
  f.flushTimers();
  assert.equal(late.style.display, "none");
  const api = f.context.window.KAFX;
  vm.runInNewContext(FILTER_SOURCE, f.context, { filename: FILTER_PATH });
  assert.equal(f.context.window.KAFX, api);
  assert.equal(f.observerCount(), 1);
});

test("Android and Userscript both load the canonical filter", () => {
  const activity = readFileSync("app/src/main/java/com/example/CleanTwitter/MainActivity.kt", "utf8");
  const userscript = readFileSync("KafXClean.user.js", "utf8");
  assert.match(activity, /assets\.open\("filter\.js"\)/);
  assert.match(activity, /prepareBack/);
  assert.match(userscript, /@require\s+https:\/\/raw\.githubusercontent\.com\/KAFKA2306\/KafXClean\/main\/app\/src\/main\/assets\/filter\.js/);
});

__KAFX_V185_8__

mkdir -p "/work/$(dirname 'KafXClean.user.js')"
cat > "/work/KafXClean.user.js" <<'__KAFX_V185_9__'
// ==UserScript==
// @name         KafXClean
// @namespace    https://github.com/KAFKA2306/KafXClean
// @version      1.4.4
// @description  Hide X's For You tab, ads, videos, reposts, and Premium purchase buttons on the Following timeline.
// @match        https://x.com/*
// @match        https://twitter.com/*
// @match        https://mobile.twitter.com/*
// @run-at       document-end
// @grant        none
// @require      https://raw.githubusercontent.com/KAFKA2306/KafXClean/main/app/src/main/assets/filter.js
// @downloadURL  https://raw.githubusercontent.com/KAFKA2306/KafXClean/main/KafXClean.user.js
// @updateURL    https://raw.githubusercontent.com/KAFKA2306/KafXClean/main/KafXClean.user.js
// ==/UserScript==

__KAFX_V185_9__

cd /work
node --check app/src/main/assets/filter.js
node --check KafXClean.user.js
node --test tests/filter-dom.test.mjs
/opt/gradle-9.6.0/bin/gradle --no-daemon --max-workers=1 :app:test :app:lint :app:assembleRelease --stacktrace

APK=/work/app/build/outputs/apk/release/app-release-unsigned.apk
test -f "$APK"
cp "$APK" /out/KafXClean-v1.8.5-unsigned.apk
echo "OK: built unsigned KafXClean v1.8.5"
