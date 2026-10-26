package com.ctf.loi;

/* compiled from: Screens.kt */
@kotlin.Metadata(k = 3, mv = {2, 0, 0}, xi = 48)
/* loaded from: classes4.dex */
final class ScreensKt$SignupScreen$1$1 implements kotlin.jvm.functions.Function3<androidx.compose.foundation.layout.ColumnScope, androidx.compose.runtime.Composer, java.lang.Integer, kotlin.Unit> {
    final /* synthetic */ android.content.Context $context;
    final /* synthetic */ androidx.compose.runtime.MutableState<java.lang.String> $email$delegate;
    final /* synthetic */ androidx.compose.runtime.MutableState<java.lang.String> $name$delegate;
    final /* synthetic */ kotlin.jvm.functions.Function0<kotlin.Unit> $onBack;
    final /* synthetic */ kotlin.jvm.functions.Function2<java.lang.String, java.lang.String, kotlin.Unit> $onSignupComplete;

    /* JADX WARN: Multi-variable type inference failed */
    ScreensKt$SignupScreen$1$1(androidx.compose.runtime.MutableState<java.lang.String> mutableState, androidx.compose.runtime.MutableState<java.lang.String> mutableState2, kotlin.jvm.functions.Function0<kotlin.Unit> function0, kotlin.jvm.functions.Function2<? super java.lang.String, ? super java.lang.String, kotlin.Unit> function2, android.content.Context context) {
        this.$name$delegate = mutableState;
        this.$email$delegate = mutableState2;
        this.$onBack = function0;
        this.$onSignupComplete = function2;
        this.$context = context;
    }

    @Override // kotlin.jvm.functions.Function3
    public /* bridge */ /* synthetic */ kotlin.Unit invoke(androidx.compose.foundation.layout.ColumnScope columnScope, androidx.compose.runtime.Composer composer, java.lang.Integer num) {
        invoke(columnScope, composer, num.intValue());
        return kotlin.Unit.INSTANCE;
    }

    /* JADX WARN: Removed duplicated region for block: B:45:0x04ea  */
    /* JADX WARN: Removed duplicated region for block: B:47:? A[RETURN, SYNTHETIC] */
    /*
        Code decompiled incorrectly, please refer to instructions dump.
        To view partially-correct add '--show-bad-code' argument
    */
    public final void invoke(androidx.compose.foundation.layout.ColumnScope r79, androidx.compose.runtime.Composer r80, int r81) {
        /*
            Method dump skipped, instructions count: 1262
            To view this dump add '--comments-level debug' option
        */
        throw new UnsupportedOperationException("Method not decompiled: com.ctf.loi.ScreensKt$SignupScreen$1$1.invoke(androidx.compose.foundation.layout.ColumnScope, androidx.compose.runtime.Composer, int):void");
    }

    /* JADX INFO: Access modifiers changed from: private */
    public static final kotlin.Unit invoke$lambda$7$lambda$1$lambda$0(androidx.compose.runtime.MutableState $name$delegate, java.lang.String it) {
        kotlin.jvm.internal.Intrinsics.checkNotNullParameter(it, "it");
        $name$delegate.setValue(it);
        return kotlin.Unit.INSTANCE;
    }

    /* JADX INFO: Access modifiers changed from: private */
    public static final kotlin.Unit invoke$lambda$7$lambda$3$lambda$2(androidx.compose.runtime.MutableState $email$delegate, java.lang.String it) {
        kotlin.jvm.internal.Intrinsics.checkNotNullParameter(it, "it");
        $email$delegate.setValue(it);
        return kotlin.Unit.INSTANCE;
    }

    /* JADX INFO: Access modifiers changed from: private */
    public static final kotlin.Unit invoke$lambda$7$lambda$6$lambda$5$lambda$4(kotlin.jvm.functions.Function2 $onSignupComplete, android.content.Context $context, androidx.compose.runtime.MutableState $name$delegate, androidx.compose.runtime.MutableState $email$delegate) {
        java.lang.String SignupScreen$lambda$34;
        java.lang.String SignupScreen$lambda$37;
        java.lang.String SignupScreen$lambda$342;
        SignupScreen$lambda$34 = com.ctf.loi.ScreensKt.SignupScreen$lambda$34($name$delegate);
        java.lang.String obj = kotlin.text.StringsKt.trim((java.lang.CharSequence) SignupScreen$lambda$34).toString();
        SignupScreen$lambda$37 = com.ctf.loi.ScreensKt.SignupScreen$lambda$37($email$delegate);
        $onSignupComplete.invoke(obj, kotlin.text.StringsKt.trim((java.lang.CharSequence) SignupScreen$lambda$37).toString());
        SignupScreen$lambda$342 = com.ctf.loi.ScreensKt.SignupScreen$lambda$34($name$delegate);
        android.widget.Toast.makeText($context, "User \"" + SignupScreen$lambda$342 + "\" created", 0).show();
        $name$delegate.setValue("");
        $email$delegate.setValue("");
        return kotlin.Unit.INSTANCE;
    }
}
