# Chapter 3 Fixed-Mapping Cache Audit

## Scope

This Route H audit revalidates the cached fixed-mapping DRO continuation file
`data\computed\cache\fixed_mapping_dro_v1_079947170b953a50.pkl` with the current seven-gate policy.
It exists because the cache contains members above 10,500 km that were not part
of the current staged gate audit.

## Outcome

- Rows audited: `57`
- Strictly accepted rows: `31`
- Strictly accepted rows above 10,500 km: `31`
- Strictly accepted rows above 11,000 km: `30`
- Best trial max abs z: `14573.103184090372` km
- Best strict accepted max abs z: `14573.103184090372` km
- Exported monotone accepted family members: `30`
- Exported monotone family best max abs z: `14573.103184090372` km

## Exported Data

- `data\computed\chapter3_fixed_mapping_cache_accepted_family.csv`
- `data\computed\chapter3_fixed_mapping_cache_accepted_validation.csv`

## Rows

- member `12`: z `10518.0166693` km, rho `1.44470635125`, strict `False`, failed `gate_1_residual; gate_2_jacobi; gate_3_phase`
- member `13`: z `10579.0868056` km, rho `1.44486338094`, strict `False`, failed `gate_7_condition`
- member `14`: z `10653.0279713` km, rho `1.44505181657`, strict `False`, failed `gate_1_residual; gate_2_jacobi; gate_3_phase`
- member `15`: z `10741.7836857` km, rho `1.44527793933`, strict `False`, failed `gate_1_residual; gate_3_phase`
- member `16`: z `10847.8295217` km, rho `1.44554928664`, strict `False`, failed `gate_3_phase`
- member `17`: z `10969.6755386` km, rho `1.44586334602`, strict `True`, failed ``
- member `18`: z `11090.4605625` km, rho `1.4461774054`, strict `True`, failed ``
- member `19`: z `11210.1550067` km, rho `1.44649146479`, strict `True`, failed ``
- member `20`: z `11328.7595675` km, rho `1.44680552417`, strict `True`, failed ``
- member `21`: z `11446.2870711` km, rho `1.44711958355`, strict `True`, failed ``
- member `22`: z `11562.7553676` km, rho `1.44743364294`, strict `True`, failed ``
- member `23`: z `11678.1841021` km, rho `1.44774770232`, strict `True`, failed ``
- member `24`: z `11792.593125` km, rho `1.4480617617`, strict `True`, failed ``
- member `25`: z `11906.0016646` km, rho `1.44837582109`, strict `True`, failed ``
- member `26`: z `12018.4278687` km, rho `1.44868988047`, strict `True`, failed ``
- member `27`: z `12129.8884932` km, rho `1.44900393985`, strict `True`, failed ``
- member `28`: z `12240.39861` km, rho `1.44931799924`, strict `True`, failed ``
- member `29`: z `12349.9714161` km, rho `1.44963205862`, strict `True`, failed ``
- member `30`: z `12458.6180392` km, rho `1.449946118`, strict `True`, failed ``
- member `31`: z `12566.3473365` km, rho `1.45026017739`, strict `True`, failed ``
- member `32`: z `12673.1654626` km, rho `1.45057423677`, strict `True`, failed ``
- member `33`: z `12779.0757768` km, rho `1.45088829615`, strict `True`, failed ``
- member `34`: z `12884.078138` km, rho `1.45120235554`, strict `True`, failed ``
- member `35`: z `12988.1685183` km, rho `1.45151641492`, strict `True`, failed ``
- member `36`: z `13091.3381635` km, rho `1.4518304743`, strict `True`, failed ``
- member `37`: z `13193.5726559` km, rho `1.45214453369`, strict `True`, failed ``
- member `38`: z `13294.8506575` km, rho `1.45245859307`, strict `False`, failed `gate_2_jacobi`
- member `39`: z `13395.1419306` km, rho `1.45277265245`, strict `True`, failed ``
- member `40`: z `13494.4053022` km, rho `1.45308671184`, strict `True`, failed ``
- member `41`: z `13592.5849728` km, rho `1.45340077122`, strict `True`, failed ``
- member `42`: z `13689.6058877` km, rho `1.4537148306`, strict `True`, failed ``
- member `43`: z `13785.3667711` km, rho `1.45402888999`, strict `True`, failed ``
- member `44`: z `13879.7297631` km, rho `1.45434294937`, strict `True`, failed ``
- member `45`: z `13972.5045003` km, rho `1.45465700875`, strict `False`, failed `gate_1_residual; gate_2_jacobi`
- member `46`: z `14027.8886231` km, rho `1.45484743595`, strict `True`, failed ``
- member `47`: z `14063.4227627` km, rho `1.45497106814`, strict `False`, failed `gate_1_residual; gate_2_jacobi`
- member `48`: z `14152.0292686` km, rho `1.45528512752`, strict `False`, failed `gate_1_residual; gate_2_jacobi`
- member `49`: z `14237.7765421` km, rho `1.4555991869`, strict `False`, failed `gate_7_condition`
- member `50`: z `14319.7292541` km, rho `1.45591324629`, strict `True`, failed ``
- member `51`: z `14399.3532015` km, rho `1.45622730567`, strict `False`, failed `gate_1_residual; gate_3_phase`
- member `52`: z `14473.8511376` km, rho `1.45654136505`, strict `False`, failed `gate_7_condition`
- member `53`: z `14535.828205` km, rho `1.45685542443`, strict `False`, failed `gate_1_residual; gate_2_jacobi; gate_3_phase`
- member `54`: z `14573.1031841` km, rho `1.45716948382`, strict `True`, failed ``
- member `55`: z `14551.8535908` km, rho `1.4574835432`, strict `False`, failed `gate_5_amplitude; gate_7_condition`
- member `56`: z `14479.744706` km, rho `1.45764057289`, strict `False`, failed `gate_3_phase; gate_5_amplitude`
- member `57`: z `14376.7253204` km, rho `1.45773479071`, strict `False`, failed `gate_1_residual; gate_2_jacobi; gate_3_phase; gate_5_amplitude`
- member `58`: z `14258.5367519` km, rho `1.4577913214`, strict `False`, failed `gate_5_amplitude`
- member `59`: z `14139.0746441` km, rho `1.45782523981`, strict `False`, failed `gate_5_amplitude; gate_7_condition`
- member `60`: z `14029.2974948` km, rho `1.45784559086`, strict `False`, failed `gate_5_amplitude`
- member `61`: z `13935.5606544` km, rho `1.45785780149`, strict `False`, failed `gate_3_phase; gate_5_amplitude`
- member `62`: z `13777.8070086` km, rho `1.45787245424`, strict `False`, failed `gate_5_amplitude`
- member `63`: z `13642.2463934` km, rho `1.45788124589`, strict `False`, failed `gate_5_amplitude`
- member `64`: z `13550.5087811` km, rho `1.45788652089`, strict `False`, failed `gate_5_amplitude; gate_7_condition`
- member `65`: z `13486.691252` km, rho `1.45788968588`, strict `False`, failed `gate_1_residual; gate_5_amplitude`
- member `66`: z `13410.8706393` km, rho `1.45789348388`, strict `False`, failed `gate_5_amplitude`
- member `67`: z `13379.5780376` km, rho `1.45789576267`, strict `False`, failed `gate_5_amplitude`
- member `68`: z `13404.1277287` km, rho `1.45789849723`, strict `True`, failed ``

## Interpretation

If this audit finds accepted rows above 10,500 km, the staged gate audit must be
updated and Chapter 4 can begin from those accepted fixed-time torus data. If
high-amplitude rows fail strict Jacobi, phase, mapping-time, or conditioning
gates, the cache remains diagnostic and cannot unlock downstream figures.
