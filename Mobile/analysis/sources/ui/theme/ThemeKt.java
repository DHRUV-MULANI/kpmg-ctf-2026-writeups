package com.ctf.loi.ui.theme;

/* compiled from: Theme.kt */
@kotlin.Metadata(d1 = {"\u0000$\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0002\n\u0002\u0010\u0002\n\u0000\n\u0002\u0010\u000b\n\u0002\b\u0002\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\b\u0002\u001a4\u0010\u0003\u001a\u00020\u00042\b\b\u0002\u0010\u0005\u001a\u00020\u00062\b\b\u0002\u0010\u0007\u001a\u00020\u00062\u0011\u0010\b\u001a\r\u0012\u0004\u0012\u00020\u00040\t¢\u0006\u0002\b\nH\u0007¢\u0006\u0002\u0010\u000b\"\u000e\u0010\u0000\u001a\u00020\u0001X\u0082\u0004¢\u0006\u0002\n\u0000\"\u000e\u0010\u0002\u001a\u00020\u0001X\u0082\u0004¢\u0006\u0002\n\u0000¨\u0006\f"}, d2 = {"DarkColorScheme", "Landroidx/compose/material3/ColorScheme;", "LightColorScheme", "LatitudeOfInjectionTheme", "", "darkTheme", "", "dynamicColor", "content", "Lkotlin/Function0;", "Landroidx/compose/runtime/Composable;", "(ZZLkotlin/jvm/functions/Function2;Landroidx/compose/runtime/Composer;II)V", "app_debug"}, k = 2, mv = {2, 0, 0}, xi = 48)
/* loaded from: classes3.dex */
public final class ThemeKt {
    private static final androidx.compose.material3.ColorScheme DarkColorScheme = androidx.compose.material3.ColorSchemeKt.m1961darkColorSchemeCXl9yA$default(com.ctf.loi.ui.theme.ColorKt.getPurple80(), 0, 0, 0, 0, com.ctf.loi.ui.theme.ColorKt.getPurpleGrey80(), 0, 0, 0, com.ctf.loi.ui.theme.ColorKt.getPink80(), 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -546, 15, null);
    private static final androidx.compose.material3.ColorScheme LightColorScheme = androidx.compose.material3.ColorSchemeKt.m1965lightColorSchemeCXl9yA$default(com.ctf.loi.ui.theme.ColorKt.getPurple40(), 0, 0, 0, 0, com.ctf.loi.ui.theme.ColorKt.getPurpleGrey40(), 0, 0, 0, com.ctf.loi.ui.theme.ColorKt.getPink40(), 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -546, 15, null);

    /* JADX INFO: Access modifiers changed from: private */
    public static final kotlin.Unit LatitudeOfInjectionTheme$lambda$0(boolean z, boolean z2, kotlin.jvm.functions.Function2 function2, int i, int i2, androidx.compose.runtime.Composer composer, int i3) {
        LatitudeOfInjectionTheme(z, z2, function2, composer, androidx.compose.runtime.RecomposeScopeImplKt.updateChangedFlags(i | 1), i2);
        return kotlin.Unit.INSTANCE;
    }

    public static final void LatitudeOfInjectionTheme(boolean darkTheme, boolean dynamicColor, final kotlin.jvm.functions.Function2<? super androidx.compose.runtime.Composer, ? super java.lang.Integer, kotlin.Unit> content, androidx.compose.runtime.Composer $composer, final int $changed, final int i) {
        boolean darkTheme2;
        boolean dynamicColor2;
        int $dirty;
        boolean darkTheme3;
        androidx.compose.material3.ColorScheme colorScheme;
        androidx.compose.runtime.Composer $composer2;
        final boolean darkTheme4;
        final boolean dynamicColor3;
        kotlin.jvm.internal.Intrinsics.checkNotNullParameter(content, "content");
        androidx.compose.runtime.Composer $composer3 = $composer.startRestartGroup(-1509502834);
        androidx.compose.runtime.ComposerKt.sourceInformation($composer3, "C(LatitudeOfInjectionTheme)P(1,2)52@1582L114:Theme.kt#7tua8z");
        int $dirty2 = $changed;
        if (($changed & 6) == 0) {
            $dirty2 |= ((i & 1) == 0 && $composer3.changed(darkTheme)) ? 4 : 2;
        }
        int i2 = i & 2;
        if (i2 != 0) {
            $dirty2 |= 48;
        } else if (($changed & 48) == 0) {
            $dirty2 |= $composer3.changed(dynamicColor) ? 32 : 16;
        }
        if ((i & 4) != 0) {
            $dirty2 |= 384;
        } else if (($changed & 384) == 0) {
            $dirty2 |= $composer3.changedInstance(content) ? 256 : 128;
        }
        if (($dirty2 & 147) == 146 && $composer3.getSkipping()) {
            $composer3.skipToGroupEnd();
            dynamicColor3 = dynamicColor;
            $composer2 = $composer3;
            darkTheme4 = darkTheme;
        } else {
            $composer3.startDefaults();
            androidx.compose.runtime.ComposerKt.sourceInformation($composer3, "37@1095L21");
            if (($changed & 1) == 0 || $composer3.getDefaultsInvalid()) {
                if ((i & 1) != 0) {
                    darkTheme2 = androidx.compose.foundation.DarkThemeKt.isSystemInDarkTheme($composer3, 0);
                    $dirty2 &= -15;
                } else {
                    darkTheme2 = darkTheme;
                }
                if (i2 != 0) {
                    $dirty = $dirty2;
                    darkTheme3 = darkTheme2;
                    dynamicColor2 = true;
                } else {
                    dynamicColor2 = dynamicColor;
                    $dirty = $dirty2;
                    darkTheme3 = darkTheme2;
                }
            } else {
                $composer3.skipToGroupEnd();
                if ((i & 1) != 0) {
                    $dirty2 &= -15;
                }
                darkTheme3 = darkTheme;
                dynamicColor2 = dynamicColor;
                $dirty = $dirty2;
            }
            $composer3.endDefaults();
            if (androidx.compose.runtime.ComposerKt.isTraceInProgress()) {
                androidx.compose.runtime.ComposerKt.traceEventStart(-1509502834, $dirty, -1, "com.ctf.loi.ui.theme.LatitudeOfInjectionTheme (Theme.kt:41)");
            }
            $composer3.startReplaceGroup(-36680609);
            androidx.compose.runtime.ComposerKt.sourceInformation($composer3, "44@1385L7");
            if (!dynamicColor2 || android.os.Build.VERSION.SDK_INT < 31) {
                colorScheme = darkTheme3 ? DarkColorScheme : LightColorScheme;
            } else {
                androidx.compose.runtime.ProvidableCompositionLocal<android.content.Context> localContext = androidx.compose.ui.platform.AndroidCompositionLocals_androidKt.getLocalContext();
                androidx.compose.runtime.ComposerKt.sourceInformationMarkerStart($composer3, 2023513938, "CC(<get-current>):CompositionLocal.kt#9igjgp");
                java.lang.Object consume = $composer3.consume(localContext);
                androidx.compose.runtime.ComposerKt.sourceInformationMarkerEnd($composer3);
                android.content.Context context = (android.content.Context) consume;
                colorScheme = darkTheme3 ? androidx.compose.material3.DynamicTonalPaletteKt.dynamicDarkColorScheme(context) : androidx.compose.material3.DynamicTonalPaletteKt.dynamicLightColorScheme(context);
            }
            $composer3.endReplaceGroup();
            androidx.compose.material3.MaterialThemeKt.MaterialTheme(colorScheme, null, com.ctf.loi.ui.theme.TypeKt.getTypography(), content, $composer3, (($dirty << 3) & 7168) | 384, 2);
            $composer2 = $composer3;
            if (androidx.compose.runtime.ComposerKt.isTraceInProgress()) {
                androidx.compose.runtime.ComposerKt.traceEventEnd();
            }
            darkTheme4 = darkTheme3;
            dynamicColor3 = dynamicColor2;
        }
        androidx.compose.runtime.ScopeUpdateScope endRestartGroup = $composer2.endRestartGroup();
        if (endRestartGroup != null) {
            endRestartGroup.updateScope(new kotlin.jvm.functions.Function2() { // from class: com.ctf.loi.ui.theme.ThemeKt$$ExternalSyntheticLambda0
                @Override // kotlin.jvm.functions.Function2
                public final java.lang.Object invoke(java.lang.Object obj, java.lang.Object obj2) {
                    kotlin.Unit LatitudeOfInjectionTheme$lambda$0;
                    LatitudeOfInjectionTheme$lambda$0 = com.ctf.loi.ui.theme.ThemeKt.LatitudeOfInjectionTheme$lambda$0(darkTheme4, dynamicColor3, content, $changed, i, (androidx.compose.runtime.Composer) obj, ((java.lang.Integer) obj2).intValue());
                    return LatitudeOfInjectionTheme$lambda$0;
                }
            });
        }
    }
}
