#include <bits/stdc++.h>

double exch[4][4] = {
	{1, 1.45, 0.52, 0.72},
	{0.7, 1, 0.31, 0.48},
	{1.95, 3.1, 1, 1.49},
	{1.34, 1.98, 0.64, 1}
};

double dp[6][4];
int par[6][4];

int main(){
	for (int i = 0; i <= 2; i++) {
		dp[0][i] = 0;
	}
	dp[0][3] = 1;
	for (int i = 1; i <= 5; i++) {
		for (int j = 0; j < 4; j++) {
			for (int k = 0; k < 4; k++) {
				if (dp[i-1][j] * exch[j][k] > dp[i][k]) {
					dp[i][k] = dp[i-1][j] * exch[j][k];
					par[i][k] = j;
				}
			}
		}
	}
	for (int i = 0; i <= 5; i++) {
		printf("%d: %.10lf\n", i, dp[i][3]);
	}
	int cur = 3;
	for (int i = 5; i > 0; i--) {
		printf("%d: %d\n", i, cur);
		cur = par[i][cur];
	}
	return 0;
}
