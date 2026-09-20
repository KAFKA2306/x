FROM ubuntu:24.04 AS build

ARG SRC_MAIN
ARG SRC_FILTER
ARG SRC_MANIFEST
ARG SRC_LAYOUT
ARG SRC_STRINGS
ARG SRC_THEMES
ARG SRC_ICON
ARG SRC_TEST
ARG SRC_DOMTEST
ARG SRC_USERSCRIPT
ARG SETTINGS
ARG ROOT_BUILD
ARG APP_BUILD
ARG GRADLE_PROPS

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jdk-headless curl unzip nodejs ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt/android-sdk/cmdline-tools \
    && curl -fL --retry 3 https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip -o /tmp/cmdline.zip \
    && unzip -q /tmp/cmdline.zip -d /tmp \
    && mv /tmp/cmdline-tools /opt/android-sdk/cmdline-tools/latest

ENV ANDROID_HOME=/opt/android-sdk
ENV ANDROID_SDK_ROOT=/opt/android-sdk
ENV PATH="$PATH:/opt/android-sdk/cmdline-tools/latest/bin:/opt/android-sdk/platform-tools"

RUN yes | sdkmanager --licenses >/dev/null 2>&1 || true
RUN sdkmanager "platforms;android-36" "build-tools;36.0.0" "platform-tools"

RUN mkdir -p /work/app/src/main/java/com/example/CleanTwitter \
    /work/app/src/main/assets \
    /work/app/src/main/res/layout \
    /work/app/src/main/res/values \
    /work/app/src/main/res/drawable \
    /work/app/src/test/java/com/example/CleanTwitter \
    /work/tests

RUN printf '%s' "$SETTINGS" > /work/settings.gradle.kts \
    && printf '%s' "$ROOT_BUILD" > /work/build.gradle.kts \
    && printf '%s' "$APP_BUILD" > /work/app/build.gradle.kts \
    && printf '%s' "$GRADLE_PROPS" > /work/gradle.properties \
    && printf '%s' "$SRC_MAIN" > /work/app/src/main/java/com/example/CleanTwitter/MainActivity.kt \
    && printf '%s' "$SRC_FILTER" > /work/app/src/main/assets/filter.js \
    && printf '%s' "$SRC_MANIFEST" > /work/app/src/main/AndroidManifest.xml \
    && printf '%s' "$SRC_LAYOUT" > /work/app/src/main/res/layout/activity_main.xml \
    && printf '%s' "$SRC_STRINGS" > /work/app/src/main/res/values/strings.xml \
    && printf '%s' "$SRC_THEMES" > /work/app/src/main/res/values/themes.xml \
    && printf '%s' "$SRC_ICON" > /work/app/src/main/res/drawable/ic_launcher_brand.xml \
    && printf '%s' "$SRC_TEST" > /work/app/src/test/java/com/example/CleanTwitter/AdBlockTest.kt \
    && printf '%s' "$SRC_DOMTEST" > /work/tests/filter-dom.test.mjs \
    && printf '%s' "$SRC_USERSCRIPT" > /work/KafXClean.user.js

WORKDIR /work
RUN node --check app/src/main/assets/filter.js \
    && node --check KafXClean.user.js \
    && node --test tests/filter-dom.test.mjs

RUN curl -fL --retry 3 https://services.gradle.org/distributions/gradle-9.6.0-bin.zip -o /tmp/gradle.zip \
    && unzip -q /tmp/gradle.zip -d /opt

RUN /opt/gradle-9.6.0/bin/gradle --no-daemon :app:test :app:lint :app:assembleRelease --stacktrace

RUN mkdir -p /out \
    && cp /work/app/build/outputs/apk/release/app-release.apk /out/KafXClean-v1.8.4.apk \
    && cd /out \
    && sha256sum KafXClean-v1.8.4.apk > KafXClean-v1.8.4.apk.sha256 \
    && printf 'KafXClean v1.8.4\nsource-merge: 513652ff43499faa1945b54143185bae76b33944\n' > BUILD-PROVENANCE.txt

FROM python:3.12-alpine
WORKDIR /srv
COPY --from=build /out/ /srv/
CMD ["sh", "-c", "python -m http.server ${PORT:-8080} --bind 0.0.0.0 --directory /srv"]
