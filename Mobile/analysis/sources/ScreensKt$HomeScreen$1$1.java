package com.ctf.loi;

/* compiled from: Screens.kt */
@kotlin.Metadata(d1 = {"\u0000\n\n\u0000\n\u0002\u0010\u0002\n\u0002\u0018\u0002\u0010\u0000\u001a\u00020\u0001*\u00020\u0002H\n"}, d2 = {"<anonymous>", "", "Lkotlinx/coroutines/CoroutineScope;"}, k = 3, mv = {2, 0, 0}, xi = 48)
@kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.ctf.loi.ScreensKt$HomeScreen$1$1", f = "Screens.kt", i = {}, l = {}, m = "invokeSuspend", n = {}, s = {})
/* loaded from: classes4.dex */
final class ScreensKt$HomeScreen$1$1 extends kotlin.coroutines.jvm.internal.SuspendLambda implements kotlin.jvm.functions.Function2<kotlinx.coroutines.CoroutineScope, kotlin.coroutines.Continuation<? super kotlin.Unit>, java.lang.Object> {
    final /* synthetic */ androidx.compose.runtime.MutableState<java.lang.Boolean> $allowed$delegate;
    final /* synthetic */ double $allowedLat;
    final /* synthetic */ double $allowedLon;
    final /* synthetic */ double $allowedRadius;
    final /* synthetic */ androidx.compose.runtime.MutableState<java.lang.Boolean> $checking$delegate;
    final /* synthetic */ androidx.activity.ComponentActivity $context;
    final /* synthetic */ com.google.android.gms.location.FusedLocationProviderClient $fusedClient;
    final /* synthetic */ kotlin.jvm.functions.Function1<java.lang.String, kotlin.Unit> $onMessage;
    final /* synthetic */ androidx.compose.runtime.MutableState<java.lang.String> $status$delegate;
    int label;

    /* JADX WARN: 'super' call moved to the top of the method (can break code semantics) */
    /* JADX WARN: Multi-variable type inference failed */
    ScreensKt$HomeScreen$1$1(kotlin.jvm.functions.Function1<? super java.lang.String, kotlin.Unit> function1, com.google.android.gms.location.FusedLocationProviderClient fusedLocationProviderClient, androidx.compose.runtime.MutableState<java.lang.Boolean> mutableState, androidx.compose.runtime.MutableState<java.lang.Boolean> mutableState2, androidx.compose.runtime.MutableState<java.lang.String> mutableState3, androidx.activity.ComponentActivity componentActivity, double d, double d2, double d3, kotlin.coroutines.Continuation<? super com.ctf.loi.ScreensKt$HomeScreen$1$1> continuation) {
        super(2, continuation);
        this.$onMessage = function1;
        this.$fusedClient = fusedLocationProviderClient;
        this.$checking$delegate = mutableState;
        this.$allowed$delegate = mutableState2;
        this.$status$delegate = mutableState3;
        this.$context = componentActivity;
        this.$allowedLat = d;
        this.$allowedLon = d2;
        this.$allowedRadius = d3;
    }

    @Override // kotlin.coroutines.jvm.internal.BaseContinuationImpl
    public final kotlin.coroutines.Continuation<kotlin.Unit> create(java.lang.Object obj, kotlin.coroutines.Continuation<?> continuation) {
        return new com.ctf.loi.ScreensKt$HomeScreen$1$1(this.$onMessage, this.$fusedClient, this.$checking$delegate, this.$allowed$delegate, this.$status$delegate, this.$context, this.$allowedLat, this.$allowedLon, this.$allowedRadius, continuation);
    }

    @Override // kotlin.jvm.functions.Function2
    public final java.lang.Object invoke(kotlinx.coroutines.CoroutineScope coroutineScope, kotlin.coroutines.Continuation<? super kotlin.Unit> continuation) {
        return ((com.ctf.loi.ScreensKt$HomeScreen$1$1) create(coroutineScope, continuation)).invokeSuspend(kotlin.Unit.INSTANCE);
    }

    @Override // kotlin.coroutines.jvm.internal.BaseContinuationImpl
    public final java.lang.Object invokeSuspend(java.lang.Object obj) {
        kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (this.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure(obj);
                com.ctf.loi.ScreensKt.HomeScreen$fetchFreshLocationThenUpdateUI(this.$onMessage, this.$fusedClient, this.$checking$delegate, this.$allowed$delegate, this.$status$delegate, this.$context, this.$allowedLat, this.$allowedLon, this.$allowedRadius);
                return kotlin.Unit.INSTANCE;
            default:
                throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
        }
    }
}
