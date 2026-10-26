package com.ctf.loi;

/* compiled from: Screens.kt */
@kotlin.Metadata(d1 = {"\u0000\n\n\u0000\n\u0002\u0010\u0002\n\u0002\u0018\u0002\u0010\u0000\u001a\u00020\u0001*\u00020\u0002H\n"}, d2 = {"<anonymous>", "", "Lkotlinx/coroutines/CoroutineScope;"}, k = 3, mv = {2, 0, 0}, xi = 48)
@kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.ctf.loi.ScreensKt$AppRoot$1$1", f = "Screens.kt", i = {}, l = {androidx.core.view.MotionEventCompat.AXIS_GENERIC_11}, m = "invokeSuspend", n = {}, s = {})
/* loaded from: classes4.dex */
final class ScreensKt$AppRoot$1$1 extends kotlin.coroutines.jvm.internal.SuspendLambda implements kotlin.jvm.functions.Function2<kotlinx.coroutines.CoroutineScope, kotlin.coroutines.Continuation<? super kotlin.Unit>, java.lang.Object> {
    final /* synthetic */ androidx.compose.material3.SnackbarHostState $snackbarHostState;
    final /* synthetic */ androidx.compose.runtime.MutableState<java.lang.String> $snackbarMessage$delegate;
    java.lang.Object L$0;
    int label;

    /* JADX WARN: 'super' call moved to the top of the method (can break code semantics) */
    ScreensKt$AppRoot$1$1(androidx.compose.runtime.MutableState<java.lang.String> mutableState, androidx.compose.material3.SnackbarHostState snackbarHostState, kotlin.coroutines.Continuation<? super com.ctf.loi.ScreensKt$AppRoot$1$1> continuation) {
        super(2, continuation);
        this.$snackbarMessage$delegate = mutableState;
        this.$snackbarHostState = snackbarHostState;
    }

    @Override // kotlin.coroutines.jvm.internal.BaseContinuationImpl
    public final kotlin.coroutines.Continuation<kotlin.Unit> create(java.lang.Object obj, kotlin.coroutines.Continuation<?> continuation) {
        return new com.ctf.loi.ScreensKt$AppRoot$1$1(this.$snackbarMessage$delegate, this.$snackbarHostState, continuation);
    }

    @Override // kotlin.jvm.functions.Function2
    public final java.lang.Object invoke(kotlinx.coroutines.CoroutineScope coroutineScope, kotlin.coroutines.Continuation<? super kotlin.Unit> continuation) {
        return ((com.ctf.loi.ScreensKt$AppRoot$1$1) create(coroutineScope, continuation)).invokeSuspend(kotlin.Unit.INSTANCE);
    }

    @Override // kotlin.coroutines.jvm.internal.BaseContinuationImpl
    public final java.lang.Object invokeSuspend(java.lang.Object $result) {
        java.lang.String AppRoot$lambda$4;
        androidx.compose.runtime.MutableState<java.lang.String> mutableState;
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (this.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure($result);
                AppRoot$lambda$4 = com.ctf.loi.ScreensKt.AppRoot$lambda$4(this.$snackbarMessage$delegate);
                if (AppRoot$lambda$4 != null) {
                    androidx.compose.material3.SnackbarHostState snackbarHostState = this.$snackbarHostState;
                    androidx.compose.runtime.MutableState<java.lang.String> mutableState2 = this.$snackbarMessage$delegate;
                    this.L$0 = mutableState2;
                    this.label = 1;
                    if (androidx.compose.material3.SnackbarHostState.showSnackbar$default(snackbarHostState, AppRoot$lambda$4, null, false, null, this, 14, null) == coroutine_suspended) {
                        return coroutine_suspended;
                    }
                    mutableState = mutableState2;
                    mutableState.setValue(null);
                }
                return kotlin.Unit.INSTANCE;
            case 1:
                mutableState = (androidx.compose.runtime.MutableState) this.L$0;
                kotlin.ResultKt.throwOnFailure($result);
                mutableState.setValue(null);
                return kotlin.Unit.INSTANCE;
            default:
                throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
        }
    }
}
