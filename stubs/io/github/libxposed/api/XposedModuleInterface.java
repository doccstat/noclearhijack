package io.github.libxposed.api;

import android.content.pm.ApplicationInfo;

/**
 * Compile-only declaration of the framework's API 102 surface, derived from Apache-2.0
 * {@code libxposed/api}. It is never packaged into the APK; the framework's real class replaces it
 * at runtime. Signatures must stay byte-exact with {@code libxposed/api} 102 or hooks die with
 * {@code NoSuchMethodError}.
 */
public interface XposedModuleInterface {
    interface ModuleLoadedParam {
        boolean isSystemServer();
        String getProcessName();
    }

    interface PackageLoadedParam {
        String getPackageName();
        ApplicationInfo getApplicationInfo();
        boolean isFirstPackage();
    }

    interface PackageReadyParam extends PackageLoadedParam {
        ClassLoader getClassLoader();
    }

    interface SystemServerStartingParam {
        ClassLoader getClassLoader();
    }

    default void onModuleLoaded(ModuleLoadedParam param) {
    }

    default void onPackageLoaded(PackageLoadedParam param) {
    }

    default void onPackageReady(PackageReadyParam param) {
    }

    default void onSystemServerStarting(SystemServerStartingParam param) {
    }
}
